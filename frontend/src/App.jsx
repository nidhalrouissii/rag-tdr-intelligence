import { useState } from 'react'
import axios from 'axios'

const API = '/api'

const DOMAINES = [
  'Santé','Education','Infrastructure','Agriculture',
  'Environnement','Finance','Juridique','Communication','Technologie','Autre'
]

const REGIONS = [
  'Afrique de l\'Ouest','Afrique Centrale','Afrique de l\'Est',
  'Maghreb','Europe','Asie','Moyen-Orient','Amérique Latine','Mondial'
]

export default function App() {
  const [question, setQuestion] = useState('')
  const [filtrePays, setFiltrePays] = useState('')
  const [filtreDomaine, setFiltreDomaine] = useState('')
  const [filtreRegion, setFiltreRegion] = useState('')
  const [topK, setTopK] = useState(5)
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState('agent')
  const [agentResultat, setAgentResultat] = useState(null)
  const [chunksResultat, setChunksResultat] = useState(null)
  const [erreur, setErreur] = useState(null)

  async function lancer() {
    if (!question.trim()) return
    setLoading(true)
    setErreur(null)
    setAgentResultat(null)
    setChunksResultat(null)

    try {
      const body = {
        question,
        top_k: topK,
        filtre_pays: filtrePays || null,
        filtre_domaine: filtreDomaine || null,
        filtre_region: filtreRegion || null,
      }

      if (mode === 'agent') {
      const agentRes = await axios.post(`${API}/agent`, body)
      setAgentResultat(agentRes.data)
      setChunksResultat(agentRes.data.sources)
    }  else {
        const chunksRes = await axios.post(`${API}/rechercher`, body)
        setChunksResultat(chunksRes.data)
      }

    } catch (e) {
      if (e.response) {
        setErreur(`Erreur serveur (${e.response.status}) — Réessaie.`)
      } else {
        setErreur("Erreur API — vérifiez que le serveur FastAPI tourne sur le port 8000.")
      }
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter') lancer()
  }

  return (
    <div style={styles.page}>
      {/* HEADER EY */}
      <div style={styles.header}>
        <div style={styles.headerInner}>
          <div style={styles.logo}>
            <span style={styles.logoEY}>EY</span>
            <span style={styles.logoText}>TdR Intelligence</span>
          </div>
          <div style={styles.headerRight}>
            Recherche de missions & profils
          </div>
        </div>
      </div>

      {/* HERO */}
      <div style={styles.hero}>
        <div style={styles.heroInner}>
          <h1 style={styles.heroTitle}>
            Trouvez les missions qui correspondent à votre profil
          </h1>
          <p style={styles.heroSubtitle}>
            Powered by Agentic RAG — {' '}
            <span style={styles.heroAccent}>100 TdR analysés</span>
          </p>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div style={styles.main}>

        {/* SEARCH BOX */}
        <div style={styles.searchBox}>
          {/* MODE TOGGLE */}
          <div style={styles.modeToggle}>
            <button
              style={mode === 'agent' ? styles.modeActive : styles.modeInactive}
              onClick={() => setMode('agent')}
            >
              🤖 Agent RAG
            </button>
            <button
              style={mode === 'rechercher' ? styles.modeActive : styles.modeInactive}
              onClick={() => setMode('rechercher')}
            >
              📄 Chunks seuls
            </button>
          </div>

          {/* INPUT */}
          <div style={styles.inputRow}>
            <textarea
              style={{...styles.input, resize: 'vertical', minHeight: 48}}
              placeholder="Ex: Quels profils pour une mission santé en Afrique ?"
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) lancer()
            }}
            rows={2}
            />
            <button style={styles.searchBtn} onClick={lancer} disabled={loading}>
              {loading ? '...' : 'Rechercher'}
            </button>
          </div>

          {/* FILTRES */}
          <div style={styles.filtresLabel}>Affiner la recherche</div>
          <div style={styles.filtres}>
            <input
              style={styles.filterInput}
              type="text"
              placeholder="🌍 Pays"
              value={filtrePays}
              onChange={e => setFiltrePays(e.target.value)}
            />
            <select
              style={styles.filterInput}
              value={filtreDomaine}
              onChange={e => setFiltreDomaine(e.target.value)}
            >
              <option value="">📂 Domaine</option>
              {DOMAINES.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
            <select
              style={styles.filterInput}
              value={filtreRegion}
              onChange={e => setFiltreRegion(e.target.value)}
            >
              <option value="">🗺️ Région</option>
              {REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
            <select
              style={styles.filterInput}
              value={topK}
              onChange={e => setTopK(Number(e.target.value))}
            >
              <option value={3}>Top 3</option>
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
            </select>
          </div>
        </div>

        {/* LOADING */}
        {loading && (
          <div style={styles.loading}>
            <div style={styles.loadingBar}>
              <div style={styles.loadingFill}></div>
            </div>
            <div style={styles.loadingSteps}>
              <span>🔄 Query expansion</span>
              <span style={{color: '#FFE600'}}>→</span>
              <span>🔍 Retrieval</span>
              <span style={{color: '#FFE600'}}>→</span>
              <span>🧠 Réflexion</span>
              <span style={{color: '#FFE600'}}>→</span>
              <span>💬 Génération</span>
            </div>
          </div>
        )}

        {/* ERREUR */}
        {erreur && <div style={styles.erreur}>{erreur}</div>}

        {/* RÉSULTATS AGENT */}
        {!loading && agentResultat && mode === 'agent' && (
          <div style={styles.results}>

            {/* Bandeau agent */}
            <div style={styles.agentBandeau}>
              <div style={styles.agentBandeauLeft}>
                <span style={styles.agentBadge}>AGENT</span>
                <span style={styles.agentInfo}>
                   Score moyen {agentResultat.reflexion.score_moyen}
                  · {agentResultat.nb_chunks} sources
                </span>
              </div>
              <span style={{
                color: agentResultat.reflexion.pertinent ? '#22c55e' : '#f59e0b',
                fontSize: 13, fontWeight: 600
              }}>
                {agentResultat.reflexion.pertinent ? '✅ Pertinent' : '⚠️ Partiel'}
              </span>
            </div>

            {/* Réponse */}
            <div style={styles.reponseBox}>
              <div style={styles.reponseHeader}>
                <div style={styles.reponseLabel}>💬 Analyse Mistral</div>
                <div style={styles.reponseNb}>{agentResultat.nb_chunks} sources consultées</div>
              </div>
              <div style={styles.reponseText}>{agentResultat.reponse}</div>
            </div>

            {/* Missions similaires */}
            {chunksResultat && chunksResultat.length > 0 && (
              <>
                <div style={styles.sourcesTitle}>
                  🔗 Missions similaires
                </div>
                <div style={styles.similarGrid}>
                  {chunksResultat.slice(0, 3).map((s, i) => (
                    <SimilarCard key={i} source={s} />
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* RÉSULTATS CHUNKS */}
        {!loading && chunksResultat && mode === 'rechercher' && (
          <div style={styles.results}>
            <div style={styles.sourcesTitle}>
              🔍 {chunksResultat.length} chunks trouvés
            </div>
            {chunksResultat.map((s, i) => (
              <MissionCard key={i} source={s} index={i + 1} />
            ))}
          </div>
        )}
      </div>

      {/* FOOTER */}
      <div style={styles.footer}>
        <span style={styles.footerEY}>EY</span> TdR Intelligence
        · Powered by Mistral + Qdrant + FastAPI
      </div>
    </div>
  )
}

function MissionCard({ source, index }) {
  const [open, setOpen] = useState(false)
  const score = source.score
  const couleur = score >= 0.7 ? '#22c55e' : score >= 0.6 ? '#f59e0b' : '#94a3b8'

  return (
    <div style={styles.missionCard}>
      {/* Header */}
      <div style={styles.missionHeader} onClick={() => setOpen(!open)}>
        <div style={styles.missionLeft}>
          <div style={styles.missionScore}>
            <div style={{...styles.scoreBar, background: couleur}}></div>
            <span style={{color: couleur, fontSize: 12, fontWeight: 700}}>{score}</span>
          </div>
          <div>
            <div style={styles.missionTitre}>{source.titre || source.filename}</div>
            <div style={styles.missionMeta}>
              {source.pays && <span style={styles.metaTag}>🌍 {source.pays}</span>}
              {source.bailleur && <span style={styles.metaTag}>🏦 {source.bailleur}</span>}
              {source.domaine && <span style={styles.metaTagDomaine}>{source.domaine}</span>}
              {source.region && <span style={styles.metaTag}>🗺️ {source.region}</span>}
            </div>
          </div>
        </div>
        <span style={styles.chevron}>{open ? '▲' : '▼'}</span>
      </div>

      {/* Profils et compétences */}
      {(source.profils_requis?.length > 0 || source.competences?.length > 0) && (
        <div style={styles.missionTags}>
          {source.profils_requis?.slice(0, 3).map((p, i) => (
            <span key={i} style={styles.profilTag}>{p}</span>
          ))}
          {source.competences?.slice(0, 3).map((c, i) => (
            <span key={i} style={styles.competenceTag}>{c}</span>
          ))}
        </div>
      )}

      {/* Texte complet si ouvert */}
      {open && (
        <div style={styles.missionTexte}>{source.texte}</div>
      )}
    </div>
  )
}

function SimilarCard({ source }) {
  const score = source.score
  const couleur = score >= 0.7 ? '#22c55e' : score >= 0.6 ? '#f59e0b' : '#94a3b8'

  // Nom lisible depuis filename
  const nom = source.filename 
    ? source.filename.replace(/\.pdf$/i, '').replace(/[_-]/g, ' ')
    : source.titre

  return (
    <div style={styles.similarCard}>
      <div style={{color: couleur, fontSize: 12, fontWeight: 700, marginBottom: 6}}>
        {score}
      </div>
      <div style={styles.similarTitre}>{nom}</div>
      <div style={styles.similarMeta}>
        {source.pays && `🌍 ${source.pays}`}
        {source.domaine && ` · ${source.domaine}`}
      </div>
    </div>
  )
}

const EY_YELLOW = '#FFE600'
const EY_BLACK = '#1A1A24'
const EY_GRAY = '#F6F6FA'
const EY_BORDER = '#E0E0E8'

const styles = {
  page: {
    fontFamily: "'Segoe UI', system-ui, sans-serif",
    background: EY_GRAY,
    flex: 1,
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    color: EY_BLACK,
  },
  header: {
    background: EY_BLACK,
    borderBottom: `3px solid ${EY_YELLOW}`,
  },
  headerInner: {
    maxWidth: 1100,
    margin: '0 auto',
    padding: '16px 24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  logoEY: {
    background: EY_YELLOW,
    color: EY_BLACK,
    fontWeight: 900,
    fontSize: 20,
    padding: '4px 10px',
    borderRadius: 2,
  },
  logoText: {
    color: '#fff',
    fontWeight: 600,
    fontSize: 16,
    letterSpacing: 1,
  },
  headerRight: {
    color: '#94a3b8',
    fontSize: 13,
  },
  hero: {
    background: EY_BLACK,
    paddingBottom: 40,
  },
  heroInner: {
    maxWidth: 1100,
    margin: '0 auto',
    padding: '32px 24px 0',
  },
  heroTitle: {
    color: '#fff',
    fontSize: 28,
    fontWeight: 700,
    marginBottom: 10,
    lineHeight: 1.3,
  },
  heroSubtitle: {
    color: '#64748b',
    fontSize: 15,
  },
  heroAccent: {
    color: EY_YELLOW,
    fontWeight: 600,
  },
  main: {
    flex: 1,
    width: '100%',
    maxWidth: 1100,
    margin: '0 auto',
    padding: '0 24px 60px',
    marginTop: -20,
  },
  searchBox: {
    background: '#fff',
    borderRadius: 8,
    padding: 28,
    marginBottom: 28,
    boxShadow: '0 2px 16px rgba(0,0,0,0.08)',
    border: `1px solid ${EY_BORDER}`,
  },
  modeToggle: {
    display: 'flex',
    gap: 8,
    marginBottom: 20,
  },
  modeActive: {
    background: EY_BLACK,
    color: EY_YELLOW,
    border: 'none',
    borderRadius: 4,
    padding: '8px 18px',
    cursor: 'pointer',
    fontWeight: 700,
    fontSize: 13,
  },
  modeInactive: {
    background: 'transparent',
    color: '#64748b',
    border: `1px solid ${EY_BORDER}`,
    borderRadius: 4,
    padding: '8px 18px',
    cursor: 'pointer',
    fontSize: 13,
  },
  inputRow: {
    display: 'flex',
    gap: 10,
    marginBottom: 20,
  },
  input: {
    flex: 1,
    border: `2px solid ${EY_BLACK}`,
    borderRadius: 4,
    padding: '12px 16px',
    color: EY_BLACK,
    fontSize: 15,
    outline: 'none',
    background: '#fff',
  },
  searchBtn: {
    background: EY_YELLOW,
    color: EY_BLACK,
    border: 'none',
    borderRadius: 4,
    padding: '12px 28px',
    fontSize: 14,
    cursor: 'pointer',
    fontWeight: 700,
    letterSpacing: 0.5,
  },
  filtresLabel: {
    fontSize: 11,
    fontWeight: 700,
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 10,
  },
  filtres: {
    display: 'flex',
    gap: 10,
    flexWrap: 'wrap',
  },
  filterInput: {
    border: `1px solid ${EY_BORDER}`,
    borderRadius: 4,
    padding: '8px 12px',
    color: EY_BLACK,
    fontSize: 13,
    flex: 1,
    minWidth: 140,
    background: '#fff',
    outline: 'none',
  },
  loading: {
    background: '#fff',
    borderRadius: 8,
    padding: 28,
    textAlign: 'center',
    border: `1px solid ${EY_BORDER}`,
    marginBottom: 20,
  },
  loadingBar: {
    height: 3,
    background: EY_BORDER,
    borderRadius: 2,
    marginBottom: 16,
    overflow: 'hidden',
  },
  loadingFill: {
    height: '100%',
    width: '60%',
    background: EY_YELLOW,
    borderRadius: 2,
    animation: 'slide 1.5s ease-in-out infinite',
  },
  loadingSteps: {
    display: 'flex',
    justifyContent: 'center',
    gap: 12,
    fontSize: 13,
    color: '#64748b',
    flexWrap: 'wrap',
  },
  erreur: {
    background: '#fff0f0',
    border: '1px solid #ef4444',
    borderRadius: 6,
    padding: 16,
    color: '#ef4444',
    marginBottom: 16,
    fontSize: 14,
  },
  results: {
    display: 'flex',
    flexDirection: 'column',
    gap: 14,
  },
  agentBandeau: {
    background: EY_BLACK,
    borderRadius: 6,
    padding: '12px 18px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  agentBandeauLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  agentBadge: {
    background: EY_YELLOW,
    color: EY_BLACK,
    fontWeight: 900,
    fontSize: 11,
    padding: '3px 8px',
    borderRadius: 2,
    letterSpacing: 1,
  },
  agentInfo: {
    color: '#94a3b8',
    fontSize: 13,
  },
  variantesBox: {
    background: '#fff',
    border: `1px solid ${EY_BORDER}`,
    borderRadius: 6,
    padding: '14px 18px',
  },
  variantesLabel: {
    fontSize: 11,
    fontWeight: 700,
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 10,
  },
  variantesList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 8,
  },
  varianteTag: {
    background: EY_BLACK,
    color: EY_YELLOW,
    fontSize: 12,
    padding: '4px 10px',
    borderRadius: 3,
    fontWeight: 600,
  },
  varianteTagAlt: {
    background: EY_GRAY,
    color: '#64748b',
    fontSize: 12,
    padding: '4px 10px',
    borderRadius: 3,
    border: `1px solid ${EY_BORDER}`,
  },
  reponseBox: {
    background: '#fff',
    border: `2px solid ${EY_BLACK}`,
    borderRadius: 6,
    padding: 24,
  },
  reponseHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  reponseLabel: {
    fontWeight: 700,
    color: EY_BLACK,
    fontSize: 15,
  },
  reponseNb: {
    fontSize: 12,
    color: '#94a3b8',
  },
  reponseText: {
    lineHeight: 1.8,
    color: '#374151',
    fontSize: 14,
    whiteSpace: 'pre-wrap',
  },
  sourcesTitle: {
    fontWeight: 700,
    fontSize: 14,
    color: EY_BLACK,
    borderLeft: `3px solid ${EY_YELLOW}`,
    paddingLeft: 10,
  },
  missionCard: {
    background: '#fff',
    border: `1px solid ${EY_BORDER}`,
    borderRadius: 6,
    overflow: 'hidden',
    transition: 'box-shadow 0.2s',
  },
  missionHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    padding: '16px 18px',
    cursor: 'pointer',
  },
  missionLeft: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 14,
    flex: 1,
  },
  missionScore: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 4,
    minWidth: 30,
  },
  scoreBar: {
    width: 3,
    height: 32,
    borderRadius: 2,
  },
  missionTitre: {
    fontWeight: 700,
    fontSize: 14,
    color: EY_BLACK,
    marginBottom: 6,
    lineHeight: 1.4,
  },
  missionMeta: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 6,
  },
  metaTag: {
    fontSize: 11,
    color: '#64748b',
    background: EY_GRAY,
    padding: '2px 8px',
    borderRadius: 3,
    border: `1px solid ${EY_BORDER}`,
  },
  metaTagDomaine: {
    fontSize: 11,
    color: EY_BLACK,
    background: EY_YELLOW,
    padding: '2px 8px',
    borderRadius: 3,
    fontWeight: 700,
  },
  missionTags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 6,
    padding: '0 18px 14px',
    borderTop: `1px solid ${EY_BORDER}`,
    paddingTop: 12,
  },
  profilTag: {
    fontSize: 11,
    background: '#f0f9ff',
    color: '#0369a1',
    border: '1px solid #bae6fd',
    padding: '3px 10px',
    borderRadius: 20,
  },
  competenceTag: {
    fontSize: 11,
    background: '#f0fdf4',
    color: '#15803d',
    border: '1px solid #bbf7d0',
    padding: '3px 10px',
    borderRadius: 20,
  },
  chevron: {
    color: '#94a3b8',
    fontSize: 11,
    marginLeft: 10,
  },
  missionTexte: {
    padding: '0 18px 18px',
    fontSize: 13,
    color: '#64748b',
    lineHeight: 1.7,
    borderTop: `1px solid ${EY_BORDER}`,
    paddingTop: 14,
    whiteSpace: 'pre-wrap',
  },
  similarGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: 12,
  },
  similarCard: {
    background: '#fff',
    border: `1px solid ${EY_BORDER}`,
    borderRadius: 6,
    padding: 16,
    borderTop: `3px solid ${EY_YELLOW}`,
  },
  similarTitre: {
    fontWeight: 600,
    fontSize: 13,
    color: EY_BLACK,
    marginBottom: 6,
    lineHeight: 1.4,
  },
  similarMeta: {
    fontSize: 11,
    color: '#94a3b8',
  },
  footer: {
    background: EY_BLACK,
    color: '#64748b',
    textAlign: 'center',
    padding: '20px 24px',
    fontSize: 13,
    borderTop: `3px solid ${EY_YELLOW}`,
  },
  footerEY: {
    background: EY_YELLOW,
    color: EY_BLACK,
    fontWeight: 900,
    fontSize: 12,
    padding: '2px 6px',
    borderRadius: 2,
    marginRight: 6,
  },
}