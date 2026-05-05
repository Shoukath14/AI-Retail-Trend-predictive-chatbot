import os
import requests
from groq import Groq

SYSTEM_PROMPT_NO_DATASET = """You are a fashion and retail trend assistant. Be conversational and brief — 2-4 sentences max unless asked for more.

STRICT RULES:
1. If web search results are provided below, use ONLY those results to answer. Use specific facts from them.
2. NEVER invent numbers, percentages, or statistics not present in the search results.
3. If the question is unrelated to fashion or retail (e.g. cooking, tech, general knowledge), reply ONLY: "I specialize only in fashion and retail trend analysis."
4. If no search results are helpful, say "I don't have current data on that — try uploading your dataset for specific insights."

Sound natural and helpful. Like texting a knowledgeable friend."""

SYSTEM_PROMPT_WITH_DATASET = """You are a fashion and retail trend assistant with access to the user's uploaded dataset.

Be conversational and brief — 2-4 sentences max unless user explicitly asks for a report or full analysis.

STRICT RULES:
- Use ONLY numbers and facts from the dataset provided. Never invent statistics.
- Only give long answers, tables, or lists if user explicitly asks (e.g. "give me a report", "full breakdown").
- If the question is unrelated to fashion or retail, reply ONLY: "I specialize only in fashion and retail trend analysis."
- If something isn't in the dataset, say so clearly instead of guessing.

Sound like a helpful analyst friend, not a formal report generator."""


def search_web(query: str) -> str:
    """Search the web using Serper and return snippet context."""
    serper_key = os.environ.get('SERPER_API_KEY', '')
    print(f"[Serper] Key: {'FOUND' if serper_key else 'MISSING'} | Query: {query}")
    if not serper_key:
        return ""
    try:
        res = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
            json={"q": query, "num": 5},
            timeout=5
        )
        print(f"[Serper] Status: {res.status_code}")
        if res.status_code != 200:
            return ""
        data = res.json()
        snippets = []
        for item in data.get("organic", [])[:5]:
            snippet = item.get("snippet", "")
            title = item.get("title", "")
            link = item.get("link", "")
            if snippet:
                snippets.append(f"- [{title}]({link}): {snippet}")
        print(f"[Serper] Snippets found: {len(snippets)}")
        return "\n".join(snippets)
    except Exception as e:
        print(f"[Serper] Error: {e}")
        return ""


def chat(messages: list, dataset_context: str = None) -> str:
    """
    Call Groq with conversation history.
    - No dataset: uses Serper for real-time web data, falls back to compound-beta
    - Dataset uploaded: uses dataset context with llama-3.3-70b-versatile
    """
    api_key = os.environ.get('GROQ_API_KEY', '')
    if not api_key:
        return "⚠️ Groq API key not configured. Please add your GROQ_API_KEY to the .env file."

    client = Groq(api_key=api_key)

    # Detect brief OR elaborate intent from last user message
    last_user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    brief_keywords = ["in brief", "briefly", "in short", "one line", "short", "summarize", "quick"]
    elaborate_keywords = ["elaborate", "explain in detail", "in detail", "full analysis", "thoroughly", "expand", "tell me more", "detailed"]

    is_brief = any(word in last_user_msg.lower() for word in brief_keywords)
    is_elaborate = any(word in last_user_msg.lower() for word in elaborate_keywords)

    if is_brief:
        max_tokens = 100
    elif is_elaborate:
        max_tokens = 1500
    else:
        max_tokens = 800

    if dataset_context:
        # Dataset mode — use llama with dataset context
        system_content = SYSTEM_PROMPT_WITH_DATASET + f"\n\nCURRENT DATASET ANALYSIS:\n{dataset_context}"
        model = "llama-3.3-70b-versatile"
        use_compound = False
    else:
        # No dataset — try Serper first, then decide model
        system_content = SYSTEM_PROMPT_NO_DATASET
        last_user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        print(f"[Search] Query: {last_user_msg}")

        web_results = search_web(last_user_msg)
        if web_results:
            # Serper worked — inject results and use llama (reliable)
            system_content += f"\n\nREAL SEARCH RESULTS FROM GOOGLE (use ONLY these for facts — never invent numbers):\n{web_results}"
            model = "llama-3.3-70b-versatile"
            use_compound = False
            print(f"[Search] Using Serper + llama | {len(web_results)} chars injected")
        else:
            # Serper failed or no results — use compound-beta for built-in web search
            model = "compound-beta"
            use_compound = True
            print("[Search] Serper unavailable, falling back to compound-beta")
    
    if is_brief:
        system_content += "\n\nIMPORTANT: User wants a VERY brief answer. Respond in ONE sentence only. No elaboration."

    if is_elaborate:
        system_content += "\n\nIMPORTANT: User wants a detailed elaborated answer. Explain thoroughly with all available facts, numbers, and insights. Use bullet points or structured format if needed."


    api_messages = [{"role": "system", "content": system_content}] + messages
    trimmed_messages = api_messages[:1] + api_messages[-10:] if len(api_messages) > 11 else api_messages

    try:
        response = client.chat.completions.create(
            model=model,
            messages=trimmed_messages,
            max_tokens=1500,
            temperature=0.4,
        )
        result = response.choices[0].message.content or ""

        # compound-beta sometimes returns empty — fall back to llama
        if use_compound and not result.strip():
            print("[compound-beta] Empty response, falling back to llama")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=trimmed_messages,
                max_tokens=1500,
                temperature=0.4,
            )
            result = response.choices[0].message.content or ""

        return result.strip()

    except Exception as e:
        err = str(e)
        print(f"[Groq] Error with {model}: {err[:100]}")

        # If compound-beta hits rate limit, fall back to llama
        if use_compound and ('rate' in err.lower() or '429' in err or 'quota' in err.lower()):
            print("[compound-beta] Rate limited, falling back to llama")
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=trimmed_messages,
                    max_tokens=1500,
                    temperature=0.4,
                )
                return (response.choices[0].message.content or "").strip()
            except Exception as e2:
                return f"⚠️ AI service error: {str(e2)}"

        # Handle 413
        if '413' in err or 'too_large' in err.lower():
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=trimmed_messages[-6:],
                    max_tokens=1500,
                    temperature=0.4,
                )
                return (response.choices[0].message.content or "").strip()
            except Exception as e2:
                return f"⚠️ AI service error: {str(e2)}"

        if 'api_key' in err.lower() or 'authentication' in err.lower():
            return "⚠️ Invalid Groq API key. Please check your .env configuration."
        elif 'quota' in err.lower() or 'rate' in err.lower():
            return "⚠️ Groq rate limit reached. Please wait a moment and try again."
        return f"⚠️ AI service error: {err}"