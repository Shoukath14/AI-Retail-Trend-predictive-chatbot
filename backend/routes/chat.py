from flask import Blueprint, request, jsonify
from models.db import get_connection
from services.chatbot import chat
import json

chat_bp = Blueprint('chat', __name__)

_analysis_cache = {}  # dataset_id -> analysis text


def set_analysis_context(dataset_id, text):
    _analysis_cache[dataset_id] = text


def get_active_context():
    if not _analysis_cache:
        return None
    latest_id = max(_analysis_cache.keys())
    return _analysis_cache[latest_id]


def clear_analysis_context():
    _analysis_cache.clear()


@chat_bp.route('/clear-context', methods=['POST'])
def clear_context():
    clear_analysis_context()
    # Clear dashboard cache in analysis module
    try:
        from routes.analysis import clear_last_analysis
        clear_last_analysis()
    except Exception:
        pass
    # Delete from database permanently
    try:
        from models.db import get_connection
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM analysis_cache")
        c.execute("DELETE FROM datasets")
        conn.commit()
        conn.close()
    except Exception:
        pass
    return jsonify({'success': True})


@chat_bp.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON body'}), 400

    user_message = data.get('message', '').strip()
    session_id = data.get('session_id')

    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400

    conn = get_connection()
    c = conn.cursor()

    # Create or validate session
    if not session_id:
        title = user_message[:50] + ('…' if len(user_message) > 50 else '')
        c.execute("INSERT INTO chat_sessions (title) VALUES (?)", (title,))
        conn.commit()
        session_id = c.lastrowid
    else:
        row = c.execute("SELECT id FROM chat_sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            c.execute("INSERT INTO chat_sessions (title) VALUES (?)", (user_message[:50],))
            conn.commit()
            session_id = c.lastrowid

    # Load conversation history (last 20 messages for context)
    rows = c.execute(
        "SELECT role, content FROM chat_messages WHERE session_id=? ORDER BY id DESC LIMIT 20",
        (session_id,)
    ).fetchall()
    history = [{'role': r['role'], 'content': r['content']} for r in reversed(rows)]
    history.append({'role': 'user', 'content': user_message})

    # Get dataset context if available
    dataset_context = get_active_context()

    # Call AI
    bot_reply = chat(history, dataset_context)

    # Persist messages
    c.execute("INSERT INTO chat_messages (session_id, role, content) VALUES (?,?,?)",
              (session_id, 'user', user_message))
    c.execute("INSERT INTO chat_messages (session_id, role, content) VALUES (?,?,?)",
              (session_id, 'assistant', bot_reply))
    c.execute("UPDATE chat_sessions SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (session_id,))
    conn.commit()
    conn.close()

    return jsonify({'reply': bot_reply, 'session_id': session_id})


@chat_bp.route('/history', methods=['GET'])
def get_history():
    conn = get_connection()
    c = conn.cursor()
    sessions = c.execute(
        "SELECT id, title, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC LIMIT 50"
    ).fetchall()
    result = [dict(s) for s in sessions]
    conn.close()
    return jsonify(result)


@chat_bp.route('/history/<int:session_id>', methods=['GET'])
def get_session_messages(session_id):
    conn = get_connection()
    c = conn.cursor()
    messages = c.execute(
        "SELECT role, content, created_at FROM chat_messages WHERE session_id=? ORDER BY id",
        (session_id,)
    ).fetchall()
    result = [dict(m) for m in messages]
    conn.close()
    return jsonify(result)


@chat_bp.route('/history/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM chat_messages WHERE session_id=?", (session_id,))
    c.execute("DELETE FROM chat_sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})
