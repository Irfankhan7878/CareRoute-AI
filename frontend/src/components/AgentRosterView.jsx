import React, { useState, useEffect } from 'react';
import { Users, CheckCircle2, ShieldCheck, Terminal, Cpu, BookOpen } from 'lucide-react';
import api from '../services/api';

export default function AgentRosterView() {
  const [roster, setRoster] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAgentStatus()
      .then(res => setRoster(res))
      .catch(err => console.error('Error fetching agent status:', err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8 pb-16">
      <div className="border-b border-slate-200 pb-4">
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">Active Multi-Agent Roster</h2>
        <p className="text-sm text-slate-600 mt-1">
          Microsoft Semantic Kernel (v1.47.0) architecture featuring 6 specialized agents with typed Python tools
        </p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 animate-pulse">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-48 bg-slate-200 rounded-3xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {roster?.agents?.map((agent, idx) => (
            <div
              key={agent.name}
              className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm hover:border-sky-300 transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 uppercase tracking-wider">
                    Agent {idx + 1}
                  </span>
                  <span className="inline-flex items-center space-x-1 text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>{agent.status}</span>
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-slate-900 text-lg">{agent.name}</h3>
                  <p className="text-xs text-slate-600 leading-relaxed mt-1">{agent.role}</p>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 space-y-2">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  Registered Python Tools
                </span>
                <div className="flex flex-col space-y-1.5">
                  {agent.tools.map((tool, tIdx) => (
                    <div
                      key={tIdx}
                      className="px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 font-mono text-[11px] text-slate-800 flex items-center justify-between"
                    >
                      <span>{tool}()</span>
                      <span className="text-[9px] font-bold text-sky-700 bg-sky-50 px-1.5 py-0.2 rounded border border-sky-100">
                        @kernel_function
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
