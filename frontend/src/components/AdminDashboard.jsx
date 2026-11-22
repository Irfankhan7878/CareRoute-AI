import React, { useState, useEffect } from 'react';
import {
  Activity,
  CheckCircle2,
  AlertOctagon,
  CalendarCheck,
  Cpu,
  RefreshCw,
  Search,
  Database,
  FileText,
  Clock,
  Terminal
} from 'lucide-react';
import api from '../services/api';

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDashboard = () => {
    setLoading(true);
    api.getAdminDashboard()
      .then(res => setData(res))
      .catch(err => setError('Failed to load admin metrics from server.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">System Admin Console</h2>
          <p className="text-sm text-slate-600">
            Real-time audit log of intake sessions, agent tool executions, and RAG retrieval activity
          </p>
        </div>

        <button
          onClick={loadDashboard}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold shadow-sm flex items-center space-x-1.5 transition-all w-fit cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-sky-600' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {loading && !data ? (
        <div className="py-16 text-center text-slate-400 flex flex-col items-center space-y-2">
          <RefreshCw className="w-8 h-8 animate-spin text-sky-600" />
          <span className="text-xs">Aggregating database audit trail...</span>
        </div>
      ) : error ? (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
          {error}
        </div>
      ) : (
        <div className="space-y-8 animate-in fade-in">
          {/* KPI Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Sessions</span>
                <Activity className="w-5 h-5 text-sky-600" />
              </div>
              <p className="text-3xl font-extrabold text-slate-900">{data.total_intake_sessions}</p>
              <p className="text-[11px] text-slate-500">Patient intakes submitted</p>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Completed Routings</span>
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              </div>
              <p className="text-3xl font-extrabold text-slate-900">{data.completed_routings}</p>
              <p className="text-[11px] text-slate-500">Routine outpatient routes</p>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-rose-200 bg-rose-50/20 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-bold uppercase tracking-wider text-rose-700">Urgent Safety Stops</span>
                <AlertOctagon className="w-5 h-5 text-rose-600" />
              </div>
              <p className="text-3xl font-extrabold text-rose-700">{data.urgent_safety_stops}</p>
              <p className="text-[11px] text-rose-600 font-medium">Emergency halts triggered</p>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Demo Bookings</span>
                <CalendarCheck className="w-5 h-5 text-teal-600" />
              </div>
              <p className="text-3xl font-extrabold text-slate-900">{data.total_appointments_booked}</p>
              <p className="text-[11px] text-slate-500">Slots reserved in SQLite</p>
            </div>
          </div>

          {/* Recent Agent Executions Table */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <Cpu className="w-5 h-5 text-sky-600" />
                <h3 className="font-bold text-slate-900 text-base">Recent Agent Executions</h3>
              </div>
              <span className="text-xs text-slate-400 font-mono">logs/agent_runs.jsonl</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-50 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                  <tr>
                    <th className="p-3">Execution ID</th>
                    <th className="p-3">Agent Name</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Duration</th>
                    <th className="p-3">Summary</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {data.recent_executions?.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="p-4 text-center text-slate-400">No agent executions logged yet.</td>
                    </tr>
                  ) : (
                    data.recent_executions.map((exec) => (
                      <tr key={exec.execution_id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="p-3 font-mono text-slate-500 truncate max-w-[120px]">{exec.execution_id}</td>
                        <td className="p-3 font-bold text-slate-900">{exec.agent_name}</td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              exec.status === 'Completed'
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : exec.status === 'Stopped for safety'
                                ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                : 'bg-slate-100 text-slate-600'
                            }`}
                          >
                            {exec.status}
                          </span>
                        </td>
                        <td className="p-3 text-slate-500">{exec.duration_ms ? `${exec.duration_ms.toFixed(1)} ms` : '-'}</td>
                        <td className="p-3 text-slate-600 truncate max-w-[280px]">{exec.output_summary || exec.input_summary}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* RAG Retrieval Activity & Tool Logs Stream */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Tool Logs */}
            <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
              <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
                <Terminal className="w-5 h-5 text-teal-600" />
                <h3 className="font-bold text-slate-900 text-base">Recent Tool Invocations</h3>
              </div>

              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                {data.recent_tool_logs?.length === 0 ? (
                  <p className="text-xs text-slate-400">No tool logs recorded yet.</p>
                ) : (
                  data.recent_tool_logs.map((tl, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs flex items-center justify-between">
                      <div>
                        <span className="font-mono font-bold text-slate-800">{tl.tool_name}()</span>
                        <span className="text-[11px] text-slate-400 block">{tl.agent_name}</span>
                      </div>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700">
                        Success
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* RAG Retrieval Activity */}
            <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
              <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
                <FileText className="w-5 h-5 text-sky-600" />
                <h3 className="font-bold text-slate-900 text-base">ChromaDB RAG Retrieval Activity</h3>
              </div>

              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                {data.rag_retrieval_activity?.length === 0 ? (
                  <p className="text-xs text-slate-400">No RAG retrieval queries recorded yet.</p>
                ) : (
                  data.rag_retrieval_activity.map((rag, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-sky-800">{rag.tool_name}</span>
                        <span className="text-[10px] text-slate-400">{rag.timestamp?.split('T')[1]?.slice(0, 8)}</span>
                      </div>
                      <p className="text-[11px] text-slate-600 truncate font-mono">
                        {rag.input_args}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
