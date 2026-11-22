import React from 'react';
import {
  CheckCircle2,
  Clock,
  AlertOctagon,
  XCircle,
  Loader2,
  Terminal,
  Cpu,
  Layers
} from 'lucide-react';

const AGENT_ORDER = [
  { name: 'Intake Agent', role: 'Input validation & database record creation' },
  { name: 'Records Memory Agent', role: 'Returning patient identification & history recall' },
  { name: 'Safety Gate Agent', role: 'Emergency red-flag screening & routing halt' },
  { name: 'Triage Router Agent', role: 'Clinical classification & department routing' },
  { name: 'Information Agent', role: 'ChromaDB semantic retrieval & grounded instructions' },
  { name: 'Appointment Agent', role: 'Available slots query & appointment booking' }
];

export default function AgentTracker({ traces = [], isRunning = false }) {
  const getStatusBadge = (status) => {
    switch (status) {
      case 'Completed':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Completed</span>
          </span>
        );
      case 'Stopped for safety':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200 animate-pulse">
            <AlertOctagon className="w-3.5 h-3.5 text-rose-600" />
            <span>Stopped for safety</span>
          </span>
        );
      case 'Running':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-50 text-sky-700 border border-sky-200">
            <Loader2 className="w-3.5 h-3.5 text-sky-600 animate-spin" />
            <span>Running</span>
          </span>
        );
      case 'Failed':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
            <XCircle className="w-3.5 h-3.5 text-red-600" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>Pending</span>
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-4">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-sky-50 text-sky-700">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-lg">Multi-Agent Execution Tracker</h3>
            <p className="text-xs text-slate-500">
              Live orchestration trace across Microsoft Semantic Kernel agents and real Python tools
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-3 py-1 rounded-full">
            {traces.length} of 6 Agents Evaluated
          </span>
        </div>
      </div>

      {/* Agents Timeline Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {AGENT_ORDER.map((spec, idx) => {
          const trace = traces.find(t => t.agent_name === spec.name);
          const currentStatus = trace ? trace.status : (isRunning && idx === traces.length ? 'Running' : 'Pending');

          return (
            <div
              key={spec.name}
              className={`p-4 rounded-2xl border transition-all ${
                trace?.status === 'Stopped for safety'
                  ? 'border-rose-300 bg-rose-50/30'
                  : trace?.status === 'Completed'
                  ? 'border-emerald-200 bg-emerald-50/10'
                  : currentStatus === 'Running'
                  ? 'border-sky-300 bg-sky-50/20 shadow-sm'
                  : 'border-slate-200 bg-slate-50/50'
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Agent {idx + 1}
                  </span>
                  <h4 className="font-bold text-slate-900 text-sm">{spec.name}</h4>
                </div>
                {getStatusBadge(currentStatus)}
              </div>

              <p className="text-xs text-slate-600 mb-3 line-clamp-1">{spec.role}</p>

              {trace ? (
                <div className="space-y-2 pt-2 border-t border-slate-100 text-[11px]">
                  {/* Tools Executed */}
                  {trace.tools_executed && trace.tools_executed.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-slate-500 font-medium">Tools Called:</span>
                      <div className="flex flex-wrap gap-1">
                        {trace.tools_executed.map((tool, tIdx) => (
                          <span
                            key={tIdx}
                            className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[10px] border border-slate-200"
                          >
                            {tool}()
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Summary */}
                  {trace.output_summary && (
                    <p className="text-slate-700 leading-snug">
                      <span className="font-semibold text-slate-500">Result: </span>
                      {trace.output_summary}
                    </p>
                  )}

                  {/* Duration & Execution ID */}
                  <div className="flex items-center justify-between text-slate-400 pt-1">
                    <span>{trace.duration_ms ? `${trace.duration_ms} ms` : '0 ms'}</span>
                    <span className="font-mono text-[10px] truncate max-w-[100px]">{trace.execution_id}</span>
                  </div>
                </div>
              ) : (
                <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-100">
                  Awaiting pipeline trigger...
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
