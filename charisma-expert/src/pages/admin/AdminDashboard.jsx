import { useEffect, useState } from 'react';
import { 
  Users, 
  FileText, 
  TrendingUp, 
  Activity, 
  ShieldCheck, 
  CreditCard,
  Loader2
} from 'lucide-react';
import { getStats } from '../../api/adminPanel';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getStats()
      .then(({ data }) => setStats(data))
      .catch((err) => setError('Failed to load system statistics.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="animate-spin text-blue-600" size={32} />
      </div>
    );
  }

  if (error || !stats) {
    return <div className="p-8 text-red-600 font-medium">{error}</div>;
  }

  // Bar chart data from backend stats.documents.by_type
  const byTypeArray = stats.documents.by_type || [];
  const docTypes = byTypeArray.map(item => item.doc_type || '');
  const docCounts = byTypeArray.map(item => item.count || 0);
  
  const barChartData = {
    labels: docTypes.length ? docTypes.map(t => t.replace('_', ' ').toUpperCase()) : ['INCIDENT', 'SEARCH', 'ARREST'],
    datasets: [
      {
        label: 'Documents Generated',
        data: docTypes.length ? docCounts : [0, 0, 0],
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderRadius: 6,
      },
    ],
  };

  const barChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
      x: { grid: { display: false } }
    }
  };

  // Mock line chart data (since the backend doesn't provide time-series)
  const lineChartData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'System Load (%)',
        data: [45, 52, 38, 65, 48, 25, 30],
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, max: 100, grid: { color: 'rgba(0,0,0,0.05)' } },
      x: { grid: { display: false } }
    }
  };

  return (
    <div className="animate-in fade-in duration-500 pb-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">System Overview</h1>
          <p className="text-gray-500 mt-1">Real-time metrics and platform health.</p>
        </div>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden group">
          <div className="absolute -right-6 -top-6 w-24 h-24 bg-blue-50 rounded-full group-hover:scale-110 transition-transform duration-500"></div>
          <div className="relative">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center">
                <Users size={24} strokeWidth={1.5} />
              </div>
            </div>
            <h3 className="text-4xl font-bold text-gray-900 mb-1">{stats.users.total}</h3>
            <p className="text-sm font-medium text-gray-500">Total Registered Officers</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden group">
          <div className="absolute -right-6 -top-6 w-24 h-24 bg-emerald-50 rounded-full group-hover:scale-110 transition-transform duration-500"></div>
          <div className="relative">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-xl flex items-center justify-center">
                <FileText size={24} strokeWidth={1.5} />
              </div>
            </div>
            <h3 className="text-4xl font-bold text-gray-900 mb-1">{stats.documents.total}</h3>
            <p className="text-sm font-medium text-gray-500">Documents Generated</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden group">
          <div className="absolute -right-6 -top-6 w-24 h-24 bg-indigo-50 rounded-full group-hover:scale-110 transition-transform duration-500"></div>
          <div className="relative">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-xl flex items-center justify-center">
                <TrendingUp size={24} strokeWidth={1.5} />
              </div>
            </div>
            <h3 className="text-4xl font-bold text-gray-900 mb-1">{stats.documents.last_30d}</h3>
            <p className="text-sm font-medium text-gray-500">Generations (Last 30 Days)</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden group">
          <div className="absolute -right-6 -top-6 w-24 h-24 bg-amber-50 rounded-full group-hover:scale-110 transition-transform duration-500"></div>
          <div className="relative">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center">
                <CreditCard size={24} strokeWidth={1.5} />
              </div>
            </div>
            <h3 className="text-4xl font-bold text-gray-900 mb-1">{stats.subscriptions.active}</h3>
            <p className="text-sm font-medium text-gray-500">Active Subscriptions</p>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Document Generation by Type (Real data) */}
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-gray-900">Generations by Module Type</h3>
          </div>
          <div className="h-64">
            <Bar data={barChartData} options={barChartOptions} />
          </div>
        </div>

        {/* AI Engine Load (Mock data) */}
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-gray-900">AI Engine Workload (7 Days)</h3>
            <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
              <Activity size={14} /> Normal
            </span>
          </div>
          <div className="h-64">
            <Line data={lineChartData} options={lineChartOptions} />
          </div>
        </div>
      </div>

    </div>
  );
}
