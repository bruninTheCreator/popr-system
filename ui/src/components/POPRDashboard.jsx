import React, { useState, useEffect } from 'react'
import {
  Play,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Search,
  LogOut,
  Download,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileText
} from 'lucide-react'

// =============================================================================
// MODO DEMO (sem backend)
// =============================================================================
const DEMO_USER = {
  username: 'admin',
  role: 'admin',
  name: 'Admin'
}

const MOCK_POS = [
  {
    id: '1',
    po_number: 'PO-1001',
    vendor_code: 'V001',
    vendor_name: 'Fornecedor Alpha',
    total_amount: 12500.5,
    currency: 'BRL',
    status: 'awaiting_approval',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    items: [
      {
        item_number: '10',
        description: 'Cabo �ptico',
        quantity: 10,
        total_price: 4500
      },
      {
        item_number: '20',
        description: 'Conector SC',
        quantity: 50,
        total_price: 8000.5
      }
    ]
  },
  {
    id: '2',
    po_number: 'PO-1002',
    vendor_code: 'V014',
    vendor_name: 'Fornecedor Beta',
    total_amount: 3200,
    currency: 'BRL',
    status: 'pending',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    items: [
      {
        item_number: '10',
        description: 'Roteador',
        quantity: 2,
        total_price: 3200
      }
    ]
  },
  {
    id: '3',
    po_number: 'PO-1003',
    vendor_code: 'V007',
    vendor_name: 'Fornecedor Gama',
    total_amount: 7800,
    currency: 'BRL',
    status: 'processing',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    items: [
      {
        item_number: '10',
        description: 'Switch 48 portas',
        quantity: 1,
        total_price: 7800
      }
    ]
  },
  {
    id: '4',
    po_number: 'PO-1004',
    vendor_code: 'V021',
    vendor_name: 'Fornecedor Delta',
    total_amount: 1500,
    currency: 'BRL',
    status: 'completed',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    items: []
  },
  {
    id: '5',
    po_number: 'PO-1005',
    vendor_code: 'V099',
    vendor_name: 'Fornecedor Epsilon',
    total_amount: 920,
    currency: 'BRL',
    status: 'error',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    items: [
      {
        item_number: '10',
        description: 'Antena setorial',
        quantity: 1,
        total_price: 920
      }
    ]
  }
]

const FLOW_LANES = [
  { id: 'automacao', title: 'Automação' },
  { id: 'popr', title: 'POPR' },
  { id: 'logistica', title: 'Logistica' },
  { id: 'suprimentos', title: 'Suprimentos' }
]

const FLOW_STEPS = [
  { lane: 'automacao', text: 'Acessar plataforma POPR', type: 'task' },
  { lane: 'automacao', text: 'Anexar colaboração', type: 'task' },

  { lane: 'popr', text: 'Salvar cronograma na base', type: 'task' },
  { lane: 'popr', text: 'Criar cronograma de PEP e reservas', type: 'task' },
  { lane: 'popr', text: 'Verificar se materiais estão disponiveis', type: 'decision' },
  { lane: 'popr', text: 'Tem estoque?', type: 'decision' },
  { lane: 'popr', text: 'Tem numero de pedido?', type: 'decision' },
  { lane: 'popr', text: 'Solicitar data prevista de entrega', type: 'task' },
  { lane: 'popr', text: 'Atualizar data da reserva', type: 'task' },
  { lane: 'popr', text: 'a data de criação da reserva?', type: 'decision' },
  { lane: 'popr', text: 'Acessar SAP', type: 'task' },
  { lane: 'popr', text: 'Reservar no SAP (PEP geral)', type: 'task' },
  { lane: 'popr', text: 'Enviar e-mail para logistica', type: 'task' },
  { lane: 'popr', text: 'Enviar e-mail para Br', type: 'task' },

  { lane: 'logistica', text: 'Programar entrega a regional', type: 'task' },

  { lane: 'suprimentos', text: 'Criar RC ou pedido', type: 'task' }
]

const API_BASE = import.meta.env.VITE_API_BASE || ''
const API_V1 = API_BASE ? `${API_BASE}/api/v1` : '/api/v1'
const LIST_STATUSES = [
  'pending',
  'processing',
  'awaiting_approval',
  'approved',
  'rejected',
  'completed',
  'error'
]
const DEMO_STORAGE_KEY = 'popr_demo_pos_v1'

// =============================================================================
// COMPONENTE: HEADER
// =============================================================================
const Header = ({ user }) => {
  return (
    <header className="header">
      <div className="header-left">
        <h1>POPR</h1>
        <p>Purchase Order Processing & Reconciliation</p>
      </div>
      <div className="header-right">
        <div className="user-chip">
          <div className="user-name">{user.name}</div>
          <div className="user-role">{user.role.toUpperCase()}</div>
        </div>
      </div>
    </header>
  )
}

// =============================================================================
// COMPONENTE: DASHBOARD STATS
// =============================================================================
const DashboardStats = ({ pos }) => {
  const stats = {
    total: pos.length,
    processing: pos.filter((p) => p.status === 'processing').length,
    awaiting: pos.filter((p) => p.status === 'awaiting_approval').length,
    completed: pos.filter((p) => p.status === 'completed').length,
    error: pos.filter((p) => p.status === 'error').length
  }

  const cards = [
    { label: 'Total', value: stats.total, icon: FileText, color: 'blue' },
    { label: 'Processando', value: stats.processing, icon: Clock, color: 'blue' },
    { label: 'Aguardando', value: stats.awaiting, icon: AlertCircle, color: 'yellow' },
    { label: 'Concluidas', value: stats.completed, icon: CheckCircle, color: 'green' },
    { label: 'Erros', value: stats.error, icon: XCircle, color: 'red' }
  ]

  return (
    <div className="stats-grid">
      {cards.map((card, idx) => {
        const Icon = card.icon
        return (
          <div key={idx} className="stat-card">
            <div className={`stat-icon ${card.color}`}>
              <Icon size={18} />
            </div>
            <div className="stat-value">{card.value}</div>
            <div className="stat-label">{card.label}</div>
          </div>
        )
      })}
    </div>
  )
}

// =============================================================================
// COMPONENTE: EXPORT BUTTONS
// =============================================================================
const ExportButtons = ({ pos }) => {
  const exportToCSV = () => {
    const headers = ['PO Number', 'Vendor', 'Amount', 'Status', 'Created At']
    const rows = pos.map((po) => [
      po.po_number,
      po.vendor_name,
      `${po.currency} ${po.total_amount}`,
      po.status,
      new Date(po.created_at).toLocaleString()
    ])

    const csv = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `popr_export_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
  }

  return (
    <div className="actions">
      <button onClick={exportToCSV} className="btn btn-green">
        <Download size={16} /> Export CSV
      </button>
    </div>
  )
}

// =============================================================================
// COMPONENTE: FLUXO DEMO
// =============================================================================
const FlowDemo = () => {
  return (
    <section className="card">
      <div className="card-header">
        <h3>Fluxo POPR (demo)</h3>
        <span className="badge">Sem backend</span>
      </div>
      <p className="muted">
        Representa��o visual do fluxo enviado. Este painel � somente demonstra��o.
      </p>
      <div className="flow">
        {FLOW_LANES.map((lane) => (
          <div key={lane.id} className="lane">
            <div className="lane-title">{lane.title}</div>
            <div className="lane-steps">
              {FLOW_STEPS.filter((s) => s.lane === lane.id).map((step, idx) => (
                <div key={`${lane.id}-${idx}`} className={`flow-step ${step.type}`}>
                  <span className="flow-dot" />
                  <span className="flow-text">{step.text}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

// =============================================================================
// COMPONENTE PRINCIPAL
// =============================================================================
const POPRDashboard = () => {
  const [user] = useState(DEMO_USER)
  const [pos, setPOs] = useState([])
  const [selectedPO, setSelectedPO] = useState(null)
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [error, setError] = useState('')
  const [backendOk, setBackendOk] = useState(false)

  useEffect(() => {
    void refreshPOs()
  }, [])

  const apiFetch = async (path, options = {}) => {
    const response = await fetch(`${API_V1}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      const message =
        (data && (data.detail?.message || data.detail || data.message)) ||
        `HTTP ${response.status}`
      throw new Error(message)
    }
    return data
  }

  const normalizePO = (po) => ({
    ...po,
    total_amount: Number(po.total_amount),
    items: (po.items || []).map((item) => ({
      ...item,
      quantity: Number(item.quantity),
      unit_price: Number(item.unit_price),
      total_price: Number(item.total_price)
    }))
  })

  const loadDemoPos = () => {
    try {
      const raw = window.localStorage.getItem(DEMO_STORAGE_KEY)
      if (!raw) return MOCK_POS.map(normalizePO)
      const parsed = JSON.parse(raw)
      if (!Array.isArray(parsed)) return MOCK_POS.map(normalizePO)
      return parsed.map(normalizePO)
    } catch {
      return MOCK_POS.map(normalizePO)
    }
  }

  const saveDemoPos = (items) => {
    try {
      window.localStorage.setItem(DEMO_STORAGE_KEY, JSON.stringify(items))
    } catch {
      // ignore storage errors (quota, privacy, etc.)
    }
  }

  const refreshPOs = async () => {
    setLoading(true)
    setError('')
    try {
      const results = await Promise.all(
        LIST_STATUSES.map((status) =>
          apiFetch(`/pos?status_filter=${encodeURIComponent(status)}`)
            .then((res) => ({ ok: true, items: res.items || [] }))
            .catch(() => ({ ok: false, items: [] }))
        )
      )

      const merged = new Map()
      results.flatMap((r) => r.items).forEach((po) => {
        merged.set(po.po_number, normalizePO(po))
      })

      const items = Array.from(merged.values()).sort((a, b) => {
        const aTime = new Date(a.updated_at || a.created_at).getTime()
        const bTime = new Date(b.updated_at || b.created_at).getTime()
        return bTime - aTime
      })

      const anyOk = results.some((r) => r.ok)
      setPOs(items.length ? items : loadDemoPos())
      setBackendOk(anyOk)
      if (!anyOk) {
        setError('Backend indisponivel, usando dados mockados')
      }
    } catch (err) {
      setBackendOk(false)
      setPOs(loadDemoPos())
      setError(err.message || 'Falha ao carregar POs do backend')
    } finally {
      setLoading(false)
    }
  }

  const updateStatus = (poNumber, status) => {
    setPOs((prev) => {
      const next = prev.map((po) =>
        po.po_number === poNumber
          ? { ...po, status, updated_at: new Date().toISOString() }
          : po
      )
      if (!backendOk) {
        saveDemoPos(next)
      }
      return next
    })
  }

  const handleProcess = async (poNumber) => {
    if (!backendOk) {
      updateStatus(poNumber, 'processing')
      setTimeout(() => updateStatus(poNumber, 'completed'), 800)
      return
    }

    setLoading(true)
    setError('')
    try {
      await apiFetch('/pos/process', {
        method: 'POST',
        body: JSON.stringify({
          po_number: poNumber,
          user: user.username,
          force_approval: false,
          skip_sap_lock: true,
          notify_on_complete: false
        })
      })
      await refreshPOs()
    } catch (err) {
      setError(err.message || 'Erro ao processar PO')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (poNumber) => {
    if (!backendOk) {
      updateStatus(poNumber, 'approved')
      setTimeout(() => updateStatus(poNumber, 'completed'), 400)
      return
    }

    setLoading(true)
    setError('')
    try {
      await apiFetch('/pos/approve', {
        method: 'POST',
        body: JSON.stringify({
          po_number: poNumber,
          approved_by: user.username,
          post_invoice: true,
          notify: false
        })
      })
      await refreshPOs()
    } catch (err) {
      setError(err.message || 'Erro ao aprovar PO')
    } finally {
      setLoading(false)
    }
  }

  const handleReject = async (poNumber) => {
    if (!backendOk) {
      updateStatus(poNumber, 'rejected')
      return
    }

    const reason = window.prompt('Motivo da rejeicao:')
    if (!reason) return

    setLoading(true)
    setError('')
    try {
      await apiFetch('/pos/reject', {
        method: 'POST',
        body: JSON.stringify({
          po_number: poNumber,
          rejected_by: user.username,
          reason,
          notify: false
        })
      })
      await refreshPOs()
    } catch (err) {
      setError(err.message || 'Erro ao rejeitar PO')
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status) => {
    const configs = {
      pending: { className: 'badge gray', label: 'Pendente' },
      processing: { className: 'badge blue', label: 'Processando' },
      awaiting_approval: { className: 'badge yellow', label: 'Aguardando' },
      completed: { className: 'badge green', label: 'Conclu�do' },
      approved: { className: 'badge green', label: 'Aprovado' },
      rejected: { className: 'badge red', label: 'Rejeitado' },
      error: { className: 'badge red', label: 'Erro' }
    }

    const config = configs[status] || configs.pending

    return <span className={config.className}>{config.label}</span>
  }

  const filteredPOs = pos.filter((po) => {
    const matchesSearch =
      po.po_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      po.vendor_name.toLowerCase().includes(searchTerm.toLowerCase())

    if (statusFilter === 'all') return matchesSearch
    return matchesSearch && po.status === statusFilter
  })

  return (
    <div className="app">
      <Header user={user} />

      <main className="main">
        <div className="demo-banner">
          {backendOk
            ? 'Backend conectado (demo SAP).'
            : 'Backend offline: usando dados mockados.'}
        </div>
        {error && <div className="demo-banner">{error}</div>}

        <DashboardStats pos={pos} />

        <FlowDemo />

        <section className="card">
          <div className="filters">
            <div className="search">
              <Search size={16} />
              <input
                type="text"
                placeholder="Buscar por PO ou fornecedor..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <div className="filter-group">
              {['all', 'processing', 'awaiting_approval', 'completed', 'error'].map(
                (s) => (
                  <button
                    key={s}
                    onClick={() => setStatusFilter(s)}
                    className={statusFilter === s ? 'pill active' : 'pill'}
                  >
                    {s === 'all' ? 'Todos' : s.replace('_', ' ')}
                  </button>
                )
              )}
            </div>

            <div className="actions">
              <button onClick={refreshPOs} className="btn btn-blue">
                <RefreshCw size={16} /> Atualizar
              </button>
              <ExportButtons pos={filteredPOs} />
            </div>
          </div>
        </section>

        <section className="card">
          <h3>Purchase Orders</h3>

          {loading && <div className="muted">Carregando...</div>}

          {!loading && filteredPOs.length === 0 && (
            <div className="empty">
              <FileText size={40} />
              <p>Nenhuma PO encontrada</p>
            </div>
          )}

          {!loading &&
            filteredPOs.map((po) => (
              <div key={po.id} className="po-card">
                <div
                  className="po-header"
                  onClick={() =>
                    setSelectedPO(selectedPO?.id === po.id ? null : po)
                  }
                >
                  <div>
                    <div className="po-title">{po.po_number}</div>
                    <div className="po-subtitle">{po.vendor_name}</div>
                  </div>

                  <div className="po-meta">
                    {getStatusBadge(po.status)}
                    <div className="po-amount">
                      {po.currency}{' '}
                      {po.total_amount?.toLocaleString('pt-BR', {
                        minimumFractionDigits: 2
                      })}
                    </div>
                    <div className="po-date">
                      {new Date(po.created_at).toLocaleString('pt-BR')}
                    </div>
                  </div>
                </div>

                <div className="po-actions">
                  {po.status === 'pending' && (
                    <button className="btn btn-blue" onClick={() => handleProcess(po.po_number)}>
                      <Play size={16} /> Processar
                    </button>
                  )}

                  {po.status === 'awaiting_approval' && (
                    <>
                      <button
                        className="btn btn-green"
                        onClick={() => handleApprove(po.po_number)}
                      >
                        <ThumbsUp size={16} /> Aprovar
                      </button>
                      <button
                        className="btn btn-red"
                        onClick={() => handleReject(po.po_number)}
                      >
                        <ThumbsDown size={16} /> Rejeitar
                      </button>
                    </>
                  )}

                  {po.status === 'error' && (
                    <button className="btn btn-yellow" onClick={() => handleProcess(po.po_number)}>
                      <RefreshCw size={16} /> Reprocessar
                    </button>
                  )}
                </div>

                {selectedPO?.id === po.id && (
                  <div className="po-details">
                    <h4>Itens da PO</h4>
                    {po.items.length === 0 ? (
                      <p className="muted">Nenhum item</p>
                    ) : (
                      <table>
                        <thead>
                          <tr>
                            <th>Item</th>
                            <th>Descri��o</th>
                            <th>Qtd</th>
                            <th>Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {po.items.map((item, idx) => (
                            <tr key={idx}>
                              <td>{item.item_number}</td>
                              <td>{item.description}</td>
                              <td>{item.quantity}</td>
                              <td>
                                {po.currency}{' '}
                                {item.total_price?.toLocaleString('pt-BR', {
                                  minimumFractionDigits: 2
                                })}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </div>
            ))}
        </section>

        <footer className="footer">
          POPR System v1.0.0 � Purchase Order Processing and Reconciliation
        </footer>
      </main>
    </div>
  )
}

export default POPRDashboard
