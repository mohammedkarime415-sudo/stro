st.markdown('<div class="titre-rag">RAG</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sous-titre">Assistant de diagnostic des pannes pour les équipes de maintenance industrielle</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="cadre">
  <div class="pipeline">
    <div class="noeud"><div class="cercle">👷</div><div class="nom">Technicien</div><div class="desc">Question</div></div>
    <div class="fleche">⇄</div>
    <div class="noeud"><div class="cercle">🤖</div><div class="nom">Framework</div><div class="desc">Recherche + prompt</div></div>
    <div class="fleche">⇄</div>
    <div class="noeud"><div class="cercle">🧠</div><div class="nom">LLM</div><div class="desc">Réponse sourcée</div></div>
    <div class="fleche">⇅</div>
    <div class="noeud"><div class="cercle">🗄️</div><div class="nom">Base vectorielle</div><div class="desc">FAISS</div></div>
    <div class="fleche">⇠</div>
    <div class="noeud"><div class="cercle">📚</div><div class="nom">Documents</div><div class="desc">Manuels + pannes</div></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# Statistiques
c1, c2, c3 = st.columns(3)
for col, val, lib in [
    (c1, st.session_state.nb_docs, "Documents"),
    (c2, st.session_state.nb_pages, "Pages extraites"),
    (c3, len(st.session_state.chunks), "Chunks indexés"),
]:
    col.markdown(
        f'<div class="stat"><div class="val">{val}</div><div class="lib">{lib}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Partie chat / conversation
# ----------------------------------------------------------------------------
st.markdown('<div class="section">💬 Conversation avec l\'assistant</div>', unsafe_allow_html=True)

if st.session_state.index is None:
    st.info(
        "Pour commencer : ajoutez vos PDF dans la barre latérale, "
        "collez votre clé Gemini, puis cliquez sur « Indexer les documents »."
    )

# Questions d'exemple
st.caption("Exemples de questions :")
cols = st.columns(2)
for i, q in enumerate(QUESTIONS_EXEMPLES):
    if cols[i % 2].button(q, key=f"ex_{i}"):
        st.session_state.question_en_attente = q

# Historique
for m in st.session_state.messages:
    avatar = "🧑‍🔧" if m["role"] == "user" else "🤖"
    with st.chat_message(m["role"], avatar=avatar):
        st.markdown(m["content"])
        if m.get("sources"):
            with st.expander("📎 Sources utilisées"):
                for s in m["sources"]:
                    st.markdown(f"**{s['source']} — page {s['page']}** · score {s['score']:.2f}")
                    st.caption(s["texte"][:400] + ("…" if len(s["texte"]) > 400 else ""))

# Saisie
saisie = st.chat_input("Décrivez la panne ou posez votre question…")
question = saisie or st.session_state.question_en_attente
st.session_state.question_en_attente = None

if question:
    historique = list(st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑‍🔧"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🤖"):
        if st.session_state.index is None:
            texte = "Veuillez d'abord indexer vos documents dans la barre latérale."
            passages = []
            st.markdown(texte)
        elif not api_key:
            texte = "Veuillez saisir votre clé API Gemini dans la barre latérale."
            passages = []
            st.markdown(texte)
        else:
            with st.spinner("Analyse de la documentation…"):
                try:
                    texte, passages = repondre(question, k, seuil, modele_llm, api_key, historique)
                except Exception as e:  # erreur API, quota, modèle introuvable…
                    texte = f"Une erreur est survenue lors de la génération : `{e}`"
                    passages = []
            st.markdown(texte)
            if passages:
                with st.expander("📎 Sources utilisées"):
                    for s in passages:
                        st.markdown(f"**{s['source']} — page {s['page']}** · score {s['score']:.2f}")
                        st.caption(s["texte"][:400] + ("…" if len(s["texte"]) > 400 else ""))

    st.session_state.messages.append(
        {"role": "assistant", "content": texte, "sources": passages}
    )