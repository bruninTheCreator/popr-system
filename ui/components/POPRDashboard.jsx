import React, { useState, useEffect } from 'react';
import { 
    Play, ThumbsUp, ThumbsDown, RefreshCw, Search, 
    LogOut, User, Download, TrendingUp, Clock,
    CheckCircle, XCircle, AlertCircle, BarChart3,
    FileText, Settings
} from 'lucide-react';

// =============================================================================
// SERVIÇO DE API (conecta com FastAPI real)
// =============================================================================
const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = {
async login(username, password) {
    // TODO: Implementar autenticação real
    return { 
        token: 'fake-jwt-token',
        user: { 
        username, 
        role: username === 'admin' ? 'admin' : username.includes('aprovador') ? 'approver' : 'viewer',
        name: username.charAt(0).toUpperCase() + username.slice(1)
    }
    };
},

async fetchPOs(status = null) {
    try {
        const url = status && status !== 'all' 
        ? `${API_BASE_URL}/pos/?status_filter=${status}`
        : `${API_BASE_URL}/pos/`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('API error');
    const data = await response.json();
    return data.items || [];
    } catch (error) {
    console.error('Failed to fetch POs:', error);
    return [];
    }
},

async processPO(poNumber, user) {
    const response = await fetch(`${API_BASE_URL}/pos/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ po_number: poNumber, user })
    });
    return response.json();
},

async approvePO(poNumber, user) {
    const response = await fetch(`${API_BASE_URL}/pos/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ po_number: poNumber, approved_by: user })
    });
    return response.json();
},

async rejectPO(poNumber, user, reason) {
    const response = await fetch(`${API_BASE_URL}/pos/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ po_number: poNumber, rejected_by: user, reason })
    });
    return response.json();
}
};

// =============================================================================
// COMPONENTE: LOGIN
// =============================================================================
const LoginScreen = ({ onLogin }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

const handleSubmit = async () => {
    if (!username || !password) {
        alert('Preencha todos os campos');
        return;
    }
    
    setLoading(true);
    
    try {
        const result = await api.login(username, password);
        onLogin(result);
    } catch (error) {
        alert('Login failed');
    } finally {
        setLoading(false);
    }
};

return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 flex items-center justify-center p-6">
        <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-md">
        <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">POPR</h1>
            <p className="text-gray-600">Purchase Order Processing & Reconciliation</p>
        </div>

        <div className="space-y-4">
            <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
                Usuário
            </label>
            <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Digite seu usuário"
            />
        </div>

        <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
                Senha
            </label>
            <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Digite sua senha"
            />
        </div>

        <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
            {loading ? 'Entrando...' : 'Entrar'}
        </button>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
            Usuários de teste:<br/>
            <span className="font-mono">admin</span> • <span className="font-mono">aprovador1</span> • <span className="font-mono">viewer1</span>
        </p>
        </div>
    </div>
    </div>
);
};

// =============================================================================
// COMPONENTE: HEADER
// =============================================================================
const Header = ({ user, onLogout }) => {
const roleColors = {
    admin: 'bg-purple-100 text-purple-800',
    approver: 'bg-blue-100 text-blue-800',
    viewer: 'bg-gray-100 text-gray-800'
};

return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div>
            <h1 className="text-2xl font-bold text-gray-900">POPR</h1>
            <p className="text-sm text-gray-600">Purchase Order Processing & Reconciliation</p>
        </div>

        <div className="flex items-center gap-4">
            <div className="text-right">
            <div className="text-sm font-medium text-gray-900">{user.name}</div>
            <div className={`text-xs px-2 py-0.5 rounded ${roleColors[user.role]}`}>
                {user.role.toUpperCase()}
            </div>
        </div>
        <button
            onClick={onLogout}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title="Sair"
            >
            <LogOut className="w-5 h-5" />
        </button>
        </div>
    </div>
    </header>
);
};

// =============================================================================
// COMPONENTE: DASHBOARD STATS
// =============================================================================
const DashboardStats = ({ pos }) => {
const stats = {
    total: pos.length,
    processing: pos.filter(p => p.status === 'processing').length,
    awaiting: pos.filter(p => p.status === 'awaiting_approval').length,
    completed: pos.filter(p => p.status === 'completed').length,
    error: pos.filter(p => p.status === 'error').length
};

const cards = [
    { label: 'Total', value: stats.total, icon: FileText, color: 'text-blue-600' },
    { label: 'Processando', value: stats.processing, icon: Clock, color: 'text-blue-600' },
    { label: 'Aguardando', value: stats.awaiting, icon: AlertCircle, color: 'text-yellow-600' },
    { label: 'Concluídas', value: stats.completed, icon: CheckCircle, color: 'text-green-600' },
    { label: 'Erros', value: stats.error, icon: XCircle, color: 'text-red-600' }
];

return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
    {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
            <div key={idx} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
                <Icon className={`w-5 h-5 ${card.color}`} />
            </div>
            <div className="text-3xl font-bold text-gray-900">{card.value}</div>
            <div className="text-sm text-gray-600">{card.label}</div>
        </div>
        );
    })}
    </div>
);
};

// =============================================================================
// COMPONENTE: EXPORT BUTTONS
// =============================================================================
const ExportButtons = ({ pos }) => {
    const exportToCSV = () => {
    const headers = ['PO Number', 'Vendor', 'Amount', 'Status', 'Created At'];
    const rows = pos.map(po => [
        po.po_number,
        po.vendor_name,
        `${po.currency} ${po.total_amount}`,
        po.status,
        new Date(po.created_at).toLocaleString()
    ]);

    const csv = [
        headers.join(','),
        ...rows.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `popr_export_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
};

return (
    <div className="flex gap-2">
        <button
        onClick={exportToCSV}
        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
        >
        <Download className="w-4 h-4" />
        Export CSV
    </button>
    </div>
);
};

// =============================================================================
// COMPONENTE PRINCIPAL
// =============================================================================
const POPRDashboard = () => {
    const [user, setUser] = useState(null);
    const [pos, setPOs] = useState([]);
    const [selectedPO, setSelectedPO] = useState(null);
    const [loading, setLoading] = useState(false);
    const [statusFilter, setStatusFilter] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');

  // Fetch POs when logged in
useEffect(() => {
    if (user) {
        loadPOs();
    }
}, [user, statusFilter]);

const loadPOs = async () => {
    setLoading(true);
    try {
        const data = await api.fetchPOs(statusFilter);
        setPOs(data);
    } catch (error) {
    console.error('Failed to load POs:', error);
    } finally {
    setLoading(false);
    }
};

  // Ações
const handleProcess = async (poNumber) => {
    if (!user) return;
    setLoading(true);
    try {
        await api.processPO(poNumber, user.username);
        alert(`✅ PO ${poNumber} processada com sucesso!`);
        loadPOs();
    } catch (error) {
    alert(`❌ Erro ao processar PO: ${error.message}`);
    } finally {
    setLoading(false);
    }
};

const handleApprove = async (poNumber) => {
    if (!user || user.role === 'viewer') {
        alert('Você não tem permissão para aprovar POs');
        return;
    }
    setLoading(true);
    try {
        await api.approvePO(poNumber, user.username);
        alert(`✅ PO ${poNumber} aprovada!`);
        loadPOs();
    } catch (error) {
        alert(`❌ Erro ao aprovar PO: ${error.message}`);
    } finally {
        setLoading(false);
    }
};

const handleReject = async (poNumber) => {
    if (!user || user.role === 'viewer') {
        alert('Você não tem permissão para rejeitar POs');
        return;
    }
    const reason = prompt('Motivo da rejeição:');
    if (!reason) return;

    setLoading(true);
    try {
        await api.rejectPO(poNumber, user.username, reason);
        alert(`❌ PO ${poNumber} rejeitada`);
        loadPOs();
    } catch (error) {
        alert(`❌ Erro ao rejeitar PO: ${error.message}`);
    } finally {
        setLoading(false);
    }
};

  // Status badge
const getStatusBadge = (status) => {
    const configs = {
        pending: { color: 'bg-gray-100 text-gray-700', label: 'Pendente' },
        processing: { color: 'bg-blue-100 text-blue-700', label: 'Processando' },
        awaiting_approval: { color: 'bg-yellow-100 text-yellow-800', label: 'Aguardando' },
        completed: { color: 'bg-green-100 text-green-700', label: 'Concluído' },
        rejected: { color: 'bg-red-100 text-red-700', label: 'Rejeitado' },
        error: { color: 'bg-red-100 text-red-700', label: 'Erro' }
    };

    const config = configs[status] || configs.pending;

    return (
        <span className={`px-3 py-1 text-xs font-medium rounded-full ${config.color}`}>
        {config.label}
        </span>
    );
};

  // Filter
const filteredPOs = pos.filter(po => {
    const matchesSearch = 
        po.po_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
        po.vendor_name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
});

  // Login screen
    if (!user) {
    return <LoginScreen onLogin={setUser} />;
}

  // Main dashboard
return (
    <div className="min-h-screen bg-gray-50">
        <Header user={user} onLogout={() => setUser(null)} />

    <main className="max-w-7xl mx-auto p-6 space-y-6">
        
        {/* Stats */}
        <DashboardStats pos={pos} />

        {/* Filters & Export */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            
            {/* Search */}
            <div className="flex-1 w-full relative">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
            <input
                type="text"
                placeholder="Buscar por PO ou fornecedor..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
            </div>

            {/* Status Filters */}
            <div className="flex gap-2 flex-wrap">
            {['all', 'processing', 'awaiting_approval', 'completed', 'error'].map(s => (
                <button
                    key={s}
                    onClick={() => setStatusFilter(s)}
                    className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                    statusFilter === s
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
                >
                    {s === 'all' ? 'Todos' : s.replace('_', ' ')}
                </button>
            ))}
            </div>

            {/* Export */}
            <ExportButtons pos={filteredPOs} />
            </div>
        </div>

        {/* PO List */}
        <div className="space-y-3">
        {loading && (
            <div className="text-center py-8 text-gray-500">
                Carregando...
            </div>
        )}

            {!loading && filteredPOs.length === 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
                <FileText className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500">Nenhuma PO encontrada</p>
            </div>
        )}

        {!loading && filteredPOs.map(po => (
            <div
                key={po.id}
                className="bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
            >
              {/* Header */}
            <div 
                className="p-4 cursor-pointer"
                onClick={() => setSelectedPO(selectedPO?.id === po.id ? null : po)}
            >
                <div className="flex justify-between items-center">
                    <div>
                        <div className="text-lg font-semibold text-gray-900">{po.po_number}</div>
                        <div className="text-sm text-gray-600">{po.vendor_name}</div>
                    </div>

                <div className="flex items-center gap-4">
                    {getStatusBadge(po.status)}
                    <div className="text-right">
                    <div className="text-lg font-semibold text-gray-900">
                        {po.currency} {po.total_amount?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                    </div>
                    <div className="text-xs text-gray-500">
                        {new Date(po.created_at).toLocaleString('pt-BR')}
                    </div>
                    </div>
                </div>
                </div>
            </div>

              {/* Actions */}
            {user.role !== 'viewer' && (
                <div className="px-4 pb-4 flex gap-2">
                    {po.status === 'pending' && (
                    <button
                        onClick={() => handleProcess(po.po_number)}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                    >
                    <Play className="w-4 h-4" /> Processar
                    </button>
                )}

                {po.status === 'awaiting_approval' && (
                    <>
                    <button
                        onClick={() => handleApprove(po.po_number)}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                    >
                        <ThumbsUp className="w-4 h-4" /> Aprovar
                    </button>
                    <button
                        onClick={() => handleReject(po.po_number)}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
                    >
                        <ThumbsDown className="w-4 h-4" /> Rejeitar
                    </button>
                    </>
                )}

                {po.status === 'error' && (
                    <button
                    onClick={() => handleProcess(po.po_number)}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors disabled:opacity-50"
                    >
                        <RefreshCw className="w-4 h-4" /> Reprocessar
                    </button>
                )}
                </div>
            )}

              {/* Details */}
            {selectedPO?.id === po.id && po.items && (
                <div className="border-t border-gray-200 p-4 bg-gray-50">
                <h4 className="font-semibold mb-3 text-gray-900">Itens da PO</h4>
                {po.items.length === 0 ? (
                    <p className="text-sm text-gray-500">Nenhum item</p>
                ) : (
                    <table className="w-full text-sm">
                        <thead className="bg-gray-100">
                        <tr className="text-left text-gray-700">
                        <th className="p-2">Item</th>
                        <th className="p-2">Descrição</th>
                        <th className="p-2 text-right">Qtd</th>
                        <th className="p-2 text-right">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {po.items.map((item, idx) => (
                            <tr key={idx} className="border-t border-gray-200">
                            <td className="p-2">{item.item_number}</td>
                            <td className="p-2">{item.description}</td>
                            <td className="p-2 text-right">{item.quantity}</td>
                            <td className="p-2 text-right font-medium">
                                {po.currency} {item.total_price?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
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
        </div>

        {/* Footer */}
        <footer className="text-center text-sm text-gray-500 py-4">
            POPR System v1.0.0 • Purchase Order Processing and Reconciliation
        </footer>
    </main>
    </div>
);
};

export default POPRDashboard;