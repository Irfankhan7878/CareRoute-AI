import React from 'react';
import {
  AlertOctagon,
  PhoneCall,
  Siren,
  Building2,
  ShieldAlert,
  ArrowRight,
  RotateCcw,
  AlertTriangle
} from 'lucide-react';

export default function UrgentCareScreen({ result, onRestart }) {
  if (!result) return null;

  const {
    patient_name,
    urgent_warning_signs = [],
    urgent_care_advisory,
    session_id
  } = result;

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in">
      {/* Critical Emergency Banner */}
      <div className="bg-rose-600 text-white p-8 sm:p-10 rounded-3xl shadow-xl space-y-6 border-4 border-rose-700">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-white/20 rounded-2xl animate-pulse">
            <AlertOctagon className="w-10 h-10 text-white" />
          </div>
          <div>
            <span className="px-2.5 py-0.5 rounded-full bg-white text-rose-700 font-extrabold text-[11px] uppercase tracking-wider">
              Safety Gate Emergency Halt
            </span>
            <h2 className="text-2xl sm:text-3xl font-black tracking-tight mt-1">
              Urgent Medical Warning Detected
            </h2>
          </div>
        </div>

        <p className="text-sm sm:text-base text-rose-100 leading-relaxed font-medium">
          Normal department intake and routine appointment scheduling have been <strong>HALTED</strong> immediately.
          Our clinical safety gate detected symptoms that warrant urgent, in-person emergency evaluation.
        </p>

        {/* Warning Signs Triggered */}
        <div className="bg-rose-950/40 p-4 rounded-2xl border border-rose-400/30 space-y-2">
          <span className="text-xs font-bold text-rose-200 uppercase tracking-wider block">
            Critical Red-Flag Indicators Matched:
          </span>
          <ul className="space-y-1.5 text-xs text-rose-100">
            {urgent_warning_signs.map((sign, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <span className="text-rose-300 font-bold">•</span>
                <span className="font-semibold">{sign}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Emergency Hotlines */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
          <div className="bg-white/10 p-3.5 rounded-xl border border-white/20 text-center">
            <span className="text-[11px] text-rose-200 block">Universal Emergency</span>
            <span className="text-xl font-black text-white">Dial 112</span>
          </div>
          <div className="bg-white/10 p-3.5 rounded-xl border border-white/20 text-center">
            <span className="text-[11px] text-rose-200 block">Ambulance Service</span>
            <span className="text-xl font-black text-white">Dial 108</span>
          </div>
          <div className="bg-white/10 p-3.5 rounded-xl border border-white/20 text-center">
            <span className="text-[11px] text-rose-200 block">National Dispatch</span>
            <span className="text-xl font-black text-white">Dial 911 / 999</span>
          </div>
        </div>
      </div>

      {/* Hospital Location & In-Person Action Card */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-5">
        <div className="flex items-center space-x-2.5 text-slate-900 border-b border-slate-100 pb-4">
          <Building2 className="w-6 h-6 text-rose-600" />
          <div>
            <h3 className="font-bold text-lg">Hospital Emergency Department Location</h3>
            <p className="text-xs text-slate-500">Dedicated acute trauma and resuscitation unit</p>
          </div>
        </div>

        <div className="space-y-3 text-xs sm:text-sm text-slate-700 leading-relaxed">
          <p>
            <strong>Where to report:</strong> Ground Floor, Red Wing, Emergency Bay (24/7/365 Open).
          </p>
          <p>
            <strong>Immediate Advice:</strong> Do NOT drive yourself if experiencing chest pain, dizziness, or difficulty breathing.
            Have a companion or emergency paramedic transport you immediately.
          </p>
          <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs">
            <strong>Important Policy:</strong> In emergency situations, medical care and patient stabilization ALWAYS precede administrative paperwork or identification documents.
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
          <span className="text-xs text-slate-400 font-mono">
            Safety Stop Session: {session_id}
          </span>

          <button
            onClick={onRestart}
            className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs flex items-center space-x-2 transition-all cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Intake Session</span>
          </button>
        </div>
      </div>
    </div>
  );
}
