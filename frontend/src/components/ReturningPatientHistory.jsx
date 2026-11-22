import React, { useState, useEffect } from 'react';
import {
  History,
  User,
  Calendar,
  Building2,
  ArrowRight,
  RefreshCw,
  Clock,
  CheckCircle2,
  Search
} from 'lucide-react';
import api from '../services/api';

export default function ReturningPatientHistory({ patientId, onSelectPreviousDept, onStartNew }) {
  const [historyData, setHistoryData] = useState(null);
  const [searchId, setSearchId] = useState(patientId || 'P-1001');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchHistory = (idToQuery) => {
    if (!idToQuery) return;
    setLoading(true);
    setError(null);
    api.getPatientHistory(idToQuery)
      .then(data => setHistoryData(data))
      .catch(err => {
        setError(err.response?.data?.detail || 'Patient record not found.');
        setHistoryData(null);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (patientId) {
      fetchHistory(patientId);
    }
  }, [patientId]);

  return (
    <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-sky-50 text-sky-700">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-lg">Returning Patient Records Memory</h3>
            <p className="text-xs text-slate-500">
              Agent 6 historical lookup of previous visits and clinical department assignments
            </p>
          </div>
        </div>

        {/* Quick Search */}
        <div className="flex items-center space-x-2">
          <input
            type="text"
            placeholder="Enter Patient ID (e.g. P-1001)"
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
          <button
            onClick={() => fetchHistory(searchId)}
            className="px-3 py-1.5 rounded-lg bg-sky-600 text-white font-bold text-xs hover:bg-sky-500 cursor-pointer"
          >
            Query Memory
          </button>
        </div>
      </div>

      {loading && (
        <div className="py-8 text-center text-slate-400 flex flex-col items-center space-y-2">
          <RefreshCw className="w-5 h-5 animate-spin text-sky-600" />
          <span className="text-xs">Querying database patient memory...</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800">
          {error}
        </div>
      )}

      {historyData && (
        <div className="space-y-5 animate-in fade-in">
          {/* Patient Overview */}
          <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div>
              <span className="text-slate-400 block mb-0.5">Patient Record</span>
              <span className="font-bold text-slate-900 text-sm">{historyData.patient_name}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">Patient ID</span>
              <span className="font-mono font-bold text-sky-700">{historyData.patient_id}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">Age</span>
              <span className="font-bold text-slate-800">{historyData.age} Years</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">Total Historical Sessions</span>
              <span className="font-bold text-slate-800">{historyData.intake_sessions?.length || 0} visits</span>
            </div>
          </div>

          {/* Previous Routing Timeline */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Previous Department Routing History
            </h4>

            {historyData.routing_history?.length === 0 ? (
              <p className="text-xs text-slate-400">No previous routing records found.</p>
            ) : (
              <div className="space-y-2.5">
                {historyData.routing_history.map((record, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-2xl border border-slate-200 bg-white hover:border-sky-300 transition-all flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-slate-900 text-sm">
                          {record.selected_department}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-sky-50 text-sky-700 font-bold text-[10px] border border-sky-100">
                          {record.department_code}
                        </span>
                        <span className="text-slate-400 text-[11px]">
                          • {record.created_at ? record.created_at.split('T')[0] : 'Past Visit'}
                        </span>
                      </div>
                      <p className="text-slate-600 line-clamp-1">{record.reason}</p>
                    </div>

                    <div className="flex items-center space-x-2 flex-shrink-0">
                      <button
                        onClick={() => onSelectPreviousDept && onSelectPreviousDept(record.department_code, record.selected_department)}
                        className="px-3 py-1.5 rounded-lg bg-sky-50 text-sky-700 hover:bg-sky-100 font-bold text-[11px] border border-sky-200 transition-colors cursor-pointer"
                      >
                        Use as Reference
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Action Choice */}
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
            <span className="text-[11px] text-slate-500">
              Note: Every new consultation undergoes fresh Safety Gate screening.
            </span>
            <button
              onClick={onStartNew}
              className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs transition-colors cursor-pointer"
            >
              Start New Assessment
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
