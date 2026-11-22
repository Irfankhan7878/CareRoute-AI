import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Brain,
  FileText,
  CalendarCheck,
  Building2,
  Clock,
  Phone,
  CheckCircle2,
  Lock,
  Sparkles
} from 'lucide-react';
import api from '../services/api';

export default function HomeDashboard({ onStartIntake }) {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDepartments()
      .then(data => setDepartments(data))
      .catch(err => console.error('Error fetching departments:', err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-10 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-sky-950 to-teal-950 text-white p-8 md:p-12 shadow-xl border border-sky-900/40">
        <div className="relative z-10 max-w-3xl space-y-6">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/20 border border-teal-400/30 text-teal-300 text-xs font-semibold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Microsoft Semantic Kernel Multi-Agent Architecture</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight leading-tight text-white">
            Hospital Patient Intake &amp; Department Routing Assistant
          </h1>

          <p className="text-slate-300 text-base sm:text-lg leading-relaxed">
            An autonomous multi-agent healthcare coordination platform. Six specialized agents analyze
            patient concerns, screen urgent red-flag warnings, retrieve grounded hospital instructions via ChromaDB RAG,
            and coordinate appointment scheduling—without clinical hallucination.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <button
              onClick={onStartIntake}
              className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-teal-500 to-sky-500 hover:from-teal-400 hover:to-sky-400 text-slate-950 font-bold text-sm shadow-lg shadow-teal-500/20 flex items-center space-x-2 transition-all transform hover:-translate-y-0.5 cursor-pointer"
            >
              <span>Begin Patient Intake</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <div className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-300">
              <Lock className="w-3.5 h-3.5 text-teal-400" />
              <span>Synthetic Demo Mode • Zero Data Shared</span>
            </div>
          </div>
        </div>
      </section>

      {/* Mandatory Non-Diagnostic Medical Notice */}
      <section className="bg-amber-50/80 border-l-4 border-amber-500 p-5 rounded-2xl shadow-sm text-amber-900 flex items-start space-x-3.5">
        <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-1 text-sm leading-relaxed">
          <p className="font-bold text-amber-950 uppercase tracking-wide text-xs">
            Important Medical &amp; Regulatory Notice
          </p>
          <p>
            CareRoute AI is strictly an administrative hospital routing and intake guidance assistant, <strong>NOT a medical diagnostic system</strong>.
            It does not diagnose conditions, interpret labs, or prescribe therapies. If you experience crushing chest pain, acute respiratory distress,
            sudden weakness, or severe hemorrhage, proceed immediately to the nearest Emergency Department or dial emergency services (112 / 911 / 108).
          </p>
        </div>
      </section>

      {/* How The Multi-Agent System Works */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">How CareRoute AI Coordinates Intake</h2>
          <p className="text-sm text-slate-600">
            A genuine multi-agent orchestration pipeline enforcing safety checks, memory recall, and RAG verification.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold text-sm">
              1
            </div>
            <h3 className="font-semibold text-slate-900 text-base">Intake &amp; Memory</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Validates input demographics, persists intake records, and recalls previous routing for returning patients.
            </p>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-rose-200 bg-rose-50/20 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center font-bold text-sm">
              2
            </div>
            <h3 className="font-semibold text-slate-900 text-base flex items-center justify-between">
              <span>Safety Gate</span>
              <span className="text-[10px] font-bold px-1.5 py-0.5 bg-rose-100 text-rose-800 rounded">Non-Bypassable</span>
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Evaluates red-flag symptoms. Halts normal routing immediately if acute life threats are identified.
            </p>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center font-bold text-sm">
              3
            </div>
            <h3 className="font-semibold text-slate-900 text-base">Triage &amp; RAG</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Maps concerns to 11 departments and performs semantic retrieval over ChromaDB for grounded intake instructions.
            </p>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-sm">
              4
            </div>
            <h3 className="font-semibold text-slate-900 text-base">Demonstration Booking</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Queries real database slots for the assigned department, guarantees conflict-free reservations, and issues booking IDs.
            </p>
          </div>
        </div>
      </section>

      {/* Supported Hospital Departments Showcase */}
      <section className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-200 pb-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Supported Hospital Departments</h2>
            <p className="text-sm text-slate-600">Explore the 11 clinical departments indexed in our knowledge base.</p>
          </div>
          <span className="text-xs font-semibold px-3 py-1 bg-slate-100 text-slate-700 rounded-full w-fit">
            {departments.length} Departments Online
          </span>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-32 bg-slate-200 rounded-2xl" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {departments.map((dept) => (
              <div
                key={dept.code}
                className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-sky-300 transition-all hover:shadow-md flex flex-col justify-between space-y-3"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 text-base">{dept.name}</span>
                    <span className="text-xs font-bold px-2 py-0.5 bg-sky-50 text-sky-700 rounded-md border border-sky-100">
                      {dept.code}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                    {dept.description}
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                  <span className="flex items-center space-x-1">
                    <Building2 className="w-3.5 h-3.5 text-slate-400" />
                    <span className="truncate max-w-[130px]">{dept.location}</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>{dept.operating_hours.split(',')[0]}</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
