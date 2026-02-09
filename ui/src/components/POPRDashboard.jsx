import React, { useState, useEffect } from 'react'
import {
  Play,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Search,
  Download,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileText,
  Package,
  Truck,
  Activity,
  Zap,
  TrendingUp
} from 'lucide-react'

// =============================================================================
// MOCK DATA
// =============================================================================
const DEMO_USER = {
  username: 'admin',
  role: 'admin',
  name: 'Admin Equatorial'
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
        description: 'Cabo ?ptico',
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
  { id: 'automacao', title: 'Automa??o' },
  { id: 'popr', title: 'POPR' },
  { id: 'logistica', title: 'Log?stica' },
  { id: 'suprimentos', title: 'Suprimentos' }
]

const FLOW_STEPS = [
  { lane: 'automacao', text: 'Acessar plataforma POPR', type: 'task' },
  { lane: 'automacao', text: 'Anexar colabora??o', type: 'task' },
  { lane: 'popr', text: 'Salvar cronograma na base', type: 'task' },
  { lane: 'popr', text: 'Criar cronograma de PEP e reservas', type: 'task' },
  { lane: 'popr', text: 'Verificar se materiais est?o dispon?veis', type: 'decision' },
  { lane: 'popr', text: 'Tem estoque?', type: 'decision' },
  { lane: 'popr', text: 'Tem n?mero de pedido?', type: 'decision' },
  { lane: 'popr', text: 'Solicitar data prevista de entrega', type: 'task' },
  { lane: 'popr', text: 'Atualizar data da reserva', type: 'task' },
  { lane: 'popr', text: 'A data de cria??o da reserva?', type: 'decision' },
  { lane: 'popr', text: 'Acessar SAP', type: 'task' },
  { lane: 'popr', text: 'Reservar no SAP (PEP geral)', type: 'task' },
  { lane: 'popr', text: 'Enviar e-mail para log?stica', type: 'task' },
  { lane: 'popr', text: 'Enviar e-mail para Br', type: 'task' },
  { lane: 'logistica', text: 'Programar entrega ? regional', type: 'task' },
  { lane: 'suprimentos', text: 'Criar RC ou pedido', type: 'task' }
]

const DEMO_STORAGE_KEY = 'popr_demo_pos_v1'
const API_BASE = import.meta.env.VITE_API_BASE || ''
const API_V1 = API_BASE ? `${API_BASE}/api/v1` : '/api/v1'
const API_ROOT = API_BASE || 'http://localhost:5174'
const LIST_STATUSES = [
  'pending',
  'processing',
  'awaiting_approval',
  'approved',
  'rejected',
  'completed',
  'error'
]

// =============================================================================
// HEADER
// =============================================================================
const Header = ({ user }) => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <div className="logo">
            <Zap size={28} strokeWidth={2.5} />
          </div>
          <div className="header-title">
            <h1>POPR System</h1>
            <p>Purchase Order Processing & Reconciliation</p>
          </div>
        </div>

        <div className="header-right">
          <div className="user-info">
            <div className="user-details">
              <span className="user-name">{user.name}</span>
              <span className="user-role">{user.role}</span>
            </div>
            <div className="user-avatar">{user.name.charAt(0)}</div>
          </div>
        </div>
      </div>
    </header>
  )
}

// =============================================================================
// STATS
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
    {
      label: 'Total de POs',
      value: stats.total,
      icon: FileText,
      color: 'primary',
      trend: '+12%'
    },
    {
      label: 'Em Processamento',
      value: stats.processing,
      icon: Activity,
      color: 'info',
      trend: '3 ativos'
    },
    {
      label: 'Aguardando Aprova??o',
      value: stats.awaiting,
      icon: Clock,
      color: 'warning',
      trend: 'Aten??o'
    },
    {
      label: 'Conclu?das',
      value: stats.completed,
      icon: CheckCircle,
      color: 'success',
      trend: '+5 hoje'
    },
    {
      label: 'Com Erro',
      value: stats.error,
      icon: AlertCircle,
      color: 'danger',
      trend: 'Revisar'
    }
  ]

  return (
    <div className="stats-grid">
      {cards.map((card, idx) => {
        const Icon = card.icon
        return (
          <div key={idx} className={`stat-card ${card.color}`}>
            <div className="stat-icon">
              <Icon size={24} />
            </div>
            <div className="stat-content">
              <div className="stat-value">{card.value}</div>
              <div className="stat-label">{card.label}</div>
              <div className="stat-trend">
                <TrendingUp size={14} />
                {card.trend}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// =============================================================================
// FLOW VISUALIZATION
// =============================================================================
const FlowDemo = () => {
  const [activeLane, setActiveLane] = useState('all')
  const [flowView, setFlowView] = useState('kanban')

  const lanes = [{ id: 'all', title: 'Vis?o Geral' }, ...FLOW_LANES]
  const filteredSteps =
    activeLane === 'all'
      ? FLOW_STEPS
      : FLOW_STEPS.filter((step) => step.lane === activeLane)

  return (
    <section className="card flow-section">
      <div className="card-header">
        <div>
          <h2>Fluxo de Processos</h2>
          <p className="subtitle">Visualiza??o do pipeline operacional POPR</p>
        </div>
        <div className="badge badge-demo">Demonstra??o</div>
      </div>

      <div className="flow-controls">
        <div className="tab-group">
          {lanes.map((lane) => (
            <button
              key={lane.id}
              className={activeLane === lane.id ? 'tab active' : 'tab'}
              onClick={() => setActiveLane(lane.id)}
            >
              {lane.title}
            </button>
          ))}
        </div>

        <div className="view-toggles">
          {['kanban', 'lista', 'timeline'].map((view) => (
            <button
              key={view}
              className={flowView === view ? 'toggle active' : 'toggle'}
              onClick={() => setFlowView(view)}
            >
              {view.charAt(0).toUpperCase() + view.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {flowView === 'kanban' && (
        <div className="flow-kanban">
          {(activeLane === 'all' ? FLOW_LANES : FLOW_LANES.filter((l) => l.id === activeLane)).map((lane) => (
            <div key={lane.id} className="kanban-column">
              <div className="column-header">
                <h3>{lane.title}</h3>
                <span className="column-count">
                  {FLOW_STEPS.filter((s) => s.lane === lane.id).length}
                </span>
              </div>
              <div className="column-items">
                {FLOW_STEPS.filter((s) => s.lane === lane.id).map((step, idx) => (
                  <div key={`${lane.id}-${idx}`} className={`flow-item ${step.type}`}>
                    <span className="item-indicator"></span>
                    <span className="item-text">{step.text}</span>
                    {step.type === 'decision' && (
                      <span className="item-badge">Decis?o</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {flowView === 'lista' && (
        <div className="flow-list">
          {filteredSteps.map((step, idx) => (
            <div key={idx} className={`list-item ${step.type}`}>
              <span className="list-number">{String(idx + 1).padStart(2, '0')}</span>
              <span className="list-text">{step.text}</span>
              <span className="list-lane">{FLOW_LANES.find(l => l.id === step.lane)?.title}</span>
              <span className={`list-type ${step.type}`}>
                {step.type === 'decision' ? 'Decis?o' : 'Tarefa'}
              </span>
            </div>
          ))}
        </div>
      )}

      {flowView === 'timeline' && (
        <div className="flow-timeline">
          {filteredSteps.map((step, idx) => (
            <div key={idx} className="timeline-item">
              <div className="timeline-marker"></div>
              <div className="timeline-content">
                <div className="timeline-header">
                  <span className="timeline-title">{step.text}</span>
                  <span className="timeline-meta">
                    {FLOW_LANES.find(l => l.id === step.lane)?.title}
                  </span>
                </div>
                <div className="timeline-type">
                  {step.type === 'decision' ? 'Ponto de Decis?o' : 'Etapa do Processo'}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

// =============================================================================
// MAIN COMPONENT
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

  const [materialId, setMaterialId] = useState('MAT-001')
  const [minimumStock, setMinimumStock] = useState(10)
  const [notifyEmail, setNotifyEmail] = useState('')
  const [materialHistory, setMaterialHistory] = useState([])
  const [materialMessage, setMaterialMessage] = useState('')
  const [materialLoading, setMaterialLoading] = useState(false)
  const [emailLogs, setEmailLogs] = useState([])
  // SAP VM connection state
  const [vmHost, setVmHost] = useState('')
  const [vmPort, setVmPort] = useState('')
  const [vmUser, setVmUser] = useState('')
  const [vmPass, setVmPass] = useState('')
  const [sapConnecting, setSapConnecting] = useState(false)
  const [sapConnected, setSapConnected] = useState(false)
  const [sapMessage, setSapMessage] = useState('')

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

  const apiFetchRoot = async (path, options = {}) => {
    const response = await fetch(`${API_ROOT}${path}`, {
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

  const pushEmailLog = (entry) => {
    setEmailLogs((prev) => [
      {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        time: new Date().toISOString(),
        ...entry
      },
      ...prev
    ].slice(0, 25))
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
      // ignore
    }
  }

  const refreshPOs = async () => {
    setLoading(true)
    setError('')
    try {
      const results = await Promise.all(
        LIST_STATUSES.map((status) =>
          apiFetch(`/pos/?status_filter=${encodeURIComponent(status)}`)
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
        setError('Backend indispon?vel, usando dados mockados')
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
      setTimeout(() => updateStatus(poNumber, 'completed'), 1200)
      pushEmailLog({
        to: notifyEmail || 'compras@equatorial.com',
        subject: `PO ${poNumber} processada (demo)`,
        status: 'enviado'
      })
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
      pushEmailLog({
        to: notifyEmail || 'compras@equatorial.com',
        subject: `PO ${poNumber} processada`,
        status: 'enviado'
      })
    } catch (err) {
      setError(err.message || 'Erro ao processar PO')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (poNumber) => {
    if (!backendOk) {
      updateStatus(poNumber, 'approved')
      setTimeout(() => updateStatus(poNumber, 'completed'), 800)
      pushEmailLog({
        to: notifyEmail || 'aprovacoes@equatorial.com',
        subject: `PO ${poNumber} aprovada (demo)`,
        status: 'enviado'
      })
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
      pushEmailLog({
        to: notifyEmail || 'aprovacoes@equatorial.com',
        subject: `PO ${poNumber} aprovada`,
        status: 'enviado'
      })
    } catch (err) {
      setError(err.message || 'Erro ao aprovar PO')
    } finally {
      setLoading(false)
    }
  }

  const handleReject = async (poNumber) => {
    if (!backendOk) {
      const reason = window.prompt('Motivo da rejei??o:')
      if (!reason) return
      updateStatus(poNumber, 'rejected')
      pushEmailLog({
        to: notifyEmail || 'aprovacoes@equatorial.com',
        subject: `PO ${poNumber} rejeitada (demo)`,
        status: 'enviado'
      })
      return
    }

    const reason = window.prompt('Motivo da rejei??o:')
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
      pushEmailLog({
        to: notifyEmail || 'aprovacoes@equatorial.com',
        subject: `PO ${poNumber} rejeitada`,
        status: 'enviado'
      })
    } catch (err) {
      setError(err.message || 'Erro ao rejeitar PO')
    } finally {
      setLoading(false)
    }
  }

  const handleConnectSAP = async () => {
    if (!vmHost) {
      setSapMessage('Informe o endereço da VM')
      return
    }

    setSapConnecting(true)
    setSapMessage('')
    try {
      if (!backendOk) {
        // demo behavior: simulate a successful connect
        setTimeout(() => {
          setSapConnected(true)
          setSapMessage('Conectado ao SAP via VM (demo)')
          pushEmailLog({
            to: notifyEmail || 'infra@equatorial.com',
            subject: `Conexão SAP (demo) com ${vmHost}`,
            status: 'registrado'
          })
        }, 900)
      } else {
        // real backend: expect an endpoint to handle VM connection
        const res = await apiFetchRoot('/sap/connect-vm', {
          method: 'POST',
          body: JSON.stringify({
            host: vmHost,
            port: vmPort || null,
            username: vmUser || null,
            password: vmPass || null
          })
        })
        setSapConnected(Boolean(res.connected))
        setSapMessage(res.message || (res.connected ? 'Conectado' : 'Falha ao conectar'))
      }
    } catch (err) {
      setSapConnected(false)
      setSapMessage(err.message || 'Erro ao tentar conectar')
    } finally {
      setSapConnecting(false)
    }
  }

  const getStatusConfig = (status) => {
    const configs = {
      pending: { label: 'Pendente', class: 'gray' },
      processing: { label: 'Processando', class: 'blue' },
      awaiting_approval: { label: 'Aguardando', class: 'yellow' },
      completed: { label: 'Conclu?do', class: 'green' },
      approved: { label: 'Aprovado', class: 'green' },
      rejected: { label: 'Rejeitado', class: 'red' },
      error: { label: 'Erro', class: 'red' }
    }
    return configs[status] || configs.pending
  }

  const filteredPOs = pos.filter((po) => {
    const matchesSearch =
      po.po_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      po.vendor_name.toLowerCase().includes(searchTerm.toLowerCase())

    if (statusFilter === 'all') return matchesSearch
    return matchesSearch && po.status === statusFilter
  })

  const exportToCSV = () => {
    const headers = ['PO Number', 'Vendor', 'Amount', 'Status', 'Created At']
    const rows = filteredPOs.map((po) => [
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
    <div className="app">
      <Header user={user} />

      <main className="main">
        <div className="page-header">
          <h1>Dashboard de Pedidos</h1>
          <p>Vis?o geral do sistema POPR</p>
        </div>

        <div className="demo-banner">
          {backendOk
            ? 'Backend conectado (demo SAP).'
            : 'Backend offline: usando dados mockados.'}
        </div>
        {error && <div className="demo-banner">{error}</div>}

        <DashboardStats pos={pos} />

        <FlowDemo />

        <section className="card material-section">
          <div className="card-header">
            <div>
              <h2>Materiais</h2>
              <p className="subtitle">Consulta de estoque e POs por material</p>
            </div>
            <div className="badge badge-demo">Demo SAP</div>
          </div>

          <div className="po-filters">
            <div className="search-input">
              <Package size={20} />
              <input
                type="text"
                placeholder="Material (ex: MAT-001)"
                value={materialId}
                onChange={(e) => setMaterialId(e.target.value)}
              />
            </div>

            <div className="search-input material-small">
              <input
                type="number"
                min="0"
                placeholder="Estoque m?nimo"
                value={minimumStock}
                onChange={(e) => setMinimumStock(Number(e.target.value))}
              />
            </div>

            <div className="search-input">
              <input
                type="email"
                placeholder="Email (opcional)"
                value={notifyEmail}
                onChange={(e) => setNotifyEmail(e.target.value)}
              />
            </div>

            <div className="material-actions">
              <button
                className="btn btn-primary"
                onClick={async () => {
                  if (!materialId) return
                  setMaterialLoading(true)
                  setMaterialMessage('')
                  try {
                    const result = await apiFetchRoot('/process-material', {
                      method: 'POST',
                      body: JSON.stringify({
                        material_id: materialId,
                        minimum_stock: minimumStock,
                        notify_email: notifyEmail || null
                      })
                    })
                    setMaterialHistory(result.history || [])
                    setMaterialMessage(result.message || 'Processado com sucesso')
                    pushEmailLog({
                      to: notifyEmail || 'logistica@equatorial.com',
                      subject: `Material ${materialId} processado`,
                      status: 'enviado'
                    })
                  } catch (err) {
                    setMaterialMessage(err.message || 'Falha ao processar material')
                  } finally {
                    setMaterialLoading(false)
                  }
                }}
              >
                <Play size={18} />
                Processar material
              </button>
              <button
                className="btn btn-secondary"
                onClick={async () => {
                  if (!materialId) return
                  setMaterialLoading(true)
                  setMaterialMessage('')
                  try {
                    const result = await apiFetchRoot(`/history/${materialId}`)
                    setMaterialHistory(result.history || [])
                    setMaterialMessage('Hist?rico carregado')
                    pushEmailLog({
                      to: notifyEmail || 'compras@equatorial.com',
                      subject: `Historico de ${materialId} consultado`,
                      status: 'registrado'
                    })
                  } catch (err) {
                    setMaterialMessage(err.message || 'Falha ao buscar hist?rico')
                  } finally {
                    setMaterialLoading(false)
                  }
                }}
              >
                <RefreshCw size={18} />
                Ver hist?rico
              </button>
            </div>
          </div>

          {materialMessage && <div className="demo-banner">{materialMessage}</div>}
          {materialLoading && <div className="material-loading">Carregando...</div>}

          {!materialLoading && materialHistory.length > 0 && (
            <div className="material-table">
              <table className="items-table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Hor?rio</th>
                  </tr>
                </thead>
                <tbody>
                  {materialHistory.map((entry, idx) => (
                    <tr key={idx}>
                      <td>{entry.status}</td>
                      <td>{new Date(entry.timestamp).toLocaleString('pt-BR')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="card sap-connection-section">
          <div className="card-header">
            <div>
              <h2>Conexão SAP (VM)</h2>
              <p className="subtitle">Conectar a uma VM para executar rotinas SAP (use com cuidado)</p>
            </div>
            <div className="badge">Conexão</div>
          </div>

          <div className="po-filters">
            <div className="search-input">
              <input
                type="text"
                placeholder="Endereço da VM (ex: 192.168.56.101)"
                value={vmHost}
                onChange={(e) => setVmHost(e.target.value)}
              />
            </div>

            <div className="search-input material-small">
              <input
                type="text"
                placeholder="Porta (opcional)"
                value={vmPort}
                onChange={(e) => setVmPort(e.target.value)}
              />
            </div>

            <div className="search-input">
              <input
                type="text"
                placeholder="Usuário (opcional)"
                value={vmUser}
                onChange={(e) => setVmUser(e.target.value)}
              />
            </div>

            <div className="search-input">
              <input
                type="password"
                placeholder="Senha (opcional)"
                value={vmPass}
                onChange={(e) => setVmPass(e.target.value)}
              />
            </div>

            <div className="material-actions">
              <button
                className="btn btn-primary"
                onClick={handleConnectSAP}
                disabled={sapConnecting}
              >
                <Play size={18} />
                {sapConnecting ? 'Conectando...' : sapConnected ? 'Reconectar' : 'Conectar via VM'}
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setSapConnected(false)
                  setSapMessage('Desconectado')
                }}
                disabled={!sapConnected}
              >
                <RefreshCw size={18} />
                Desconectar
              </button>
            </div>
          </div>

          {sapMessage && <div className="demo-banner">{sapMessage}</div>}

        </section>

        <section className="card email-section">
          <div className="card-header">
            <div>
              <h2>Central de Emails</h2>
              <p className="subtitle">Registro das notificacoes enviadas pelo fluxo</p>
            </div>
            <div className="badge badge-demo">Demo</div>
          </div>

          <div className="email-list">
            {emailLogs.length === 0 && (
              <div className="empty-state">
                <FileText size={48} />
                <p>Nenhum email registrado</p>
                <span>As acoes de PO e materiais geram registros aqui</span>
              </div>
            )}

            {emailLogs.map((email) => (
              <div key={email.id} className="email-item">
                <div className="email-left">
                  <div className="email-subject">{email.subject}</div>
                  <div className="email-meta">
                    Para: {email.to} • {new Date(email.time).toLocaleString('pt-BR')}
                  </div>
                </div>
                <span className={`email-status ${email.status}`}>
                  {email.status}
                </span>
              </div>
            ))}
          </div>
        </section>

        <section className="card po-section">
          <div className="card-header">
            <div>
              <h2>Purchase Orders</h2>
              <p className="subtitle">Gest?o de pedidos de compra</p>
            </div>
            <button className="btn btn-secondary" onClick={exportToCSV}>
              <Download size={18} />
              Exportar CSV
            </button>
          </div>

          <div className="po-filters">
            <div className="search-input">
              <Search size={20} />
              <input
                type="text"
                placeholder="Buscar por PO ou fornecedor..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <div className="filter-group">
              {[
                { id: 'all', label: 'Todos' },
                { id: 'processing', label: 'Processando' },
                { id: 'awaiting_approval', label: 'Aguardando' },
                { id: 'completed', label: 'Conclu?das' },
                { id: 'error', label: 'Erros' }
              ].map((filter) => (
                <button
                  key={filter.id}
                  onClick={() => setStatusFilter(filter.id)}
                  className={statusFilter === filter.id ? 'filter-btn active' : 'filter-btn'}
                >
                  {filter.label}
                </button>
              ))}
            </div>

            <button className="btn btn-primary" onClick={refreshPOs}>
              <RefreshCw size={18} />
              Atualizar
            </button>
          </div>

          {loading && <div className="material-loading">Carregando...</div>}

          {!loading && filteredPOs.length === 0 && (
            <div className="empty-state">
              <FileText size={48} />
              <p>Nenhuma PO encontrada</p>
              <span>Tente ajustar os filtros de busca</span>
            </div>
          )}

          <div className="po-list">
            {filteredPOs.map((po) => {
              const statusConfig = getStatusConfig(po.status)
              const isExpanded = selectedPO?.id === po.id

              return (
                <div key={po.id} className="po-card">
                  <div
                    className="po-header"
                    onClick={() => setSelectedPO(isExpanded ? null : po)}
                  >
                    <div className="po-main">
                      <div className="po-number">{po.po_number}</div>
                      <div className="po-vendor">{po.vendor_name}</div>
                    </div>
                    <div className="po-info">
                      <span className={`po-status ${statusConfig.class}`}>
                        {statusConfig.label}
                      </span>
                      <div className="po-amount">
                        <span className="currency">{po.currency}</span>
                        <span className="value">
                          {po.total_amount?.toLocaleString('pt-BR', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                          })}
                        </span>
                      </div>
                      <div className="po-date">
                        {new Date(po.created_at).toLocaleDateString('pt-BR')}
                      </div>
                    </div>
                  </div>

                  <div className="po-actions">
                    {po.status === 'pending' && (
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => handleProcess(po.po_number)}
                      >
                        <Play size={16} />
                        Processar
                      </button>
                    )}

                    {po.status === 'awaiting_approval' && (
                      <>
                        <button
                          className="btn btn-success btn-sm"
                          onClick={() => handleApprove(po.po_number)}
                        >
                          <ThumbsUp size={16} />
                          Aprovar
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleReject(po.po_number)}
                        >
                          <ThumbsDown size={16} />
                          Rejeitar
                        </button>
                      </>
                    )}

                    {po.status === 'error' && (
                      <button
                        className="btn btn-warning btn-sm"
                        onClick={() => handleProcess(po.po_number)}
                      >
                        <RefreshCw size={16} />
                        Reprocessar
                      </button>
                    )}
                  </div>

                  {isExpanded && po.items.length > 0 && (
                    <div className="po-details">
                      <h4>Itens do Pedido</h4>
                      <table className="items-table">
                        <thead>
                          <tr>
                            <th>Item</th>
                            <th>Descri??o</th>
                            <th>Quantidade</th>
                            <th>Valor Total</th>
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
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </section>

        <footer className="footer">
          <p>POPR System ? {new Date().getFullYear()} Equatorial Energia</p>
          <p>Purchase Order Processing & Reconciliation - v1.0.0</p>
        </footer>
      </main>
    </div>
  )
}

export default POPRDashboard
