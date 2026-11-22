import React from 'react';
import {
  Building2,
  CheckCircle2,
  FileCheck,
  AlertCircle,
  FileText,
  User,
  Calendar,
  Compass,
  Sparkles,
  BookOpen,
  ArrowRight
} from 'lucide-react';

export default function RoutingResults({ result, onProceedToBooking }) {
  if (!result) return null;

  const {
    patient_name,
    patient_id,
    age,
    described_concern,
    selected_department,
    department_code,
    confidence_score,
    routing_reason,
    alternative_department,
    department_description,
    intake_instructions,
    documents_required = [],
    preparation_instructions = [],
    source_references = [],
    returning_patient_context
  } = result;

  const confidencePercentage = Math.round((confidence_score || 0.85) * 100);

  return (
    <div className="space-y-8">
      {/* Returning Patient Reference Banner */}
      {returning_patient_context?.is_returning && (
        <div className="bg-sky-50 border border-sky-200 rounded-2xl p-4 flex items-start space-x-3 text-sky-900">
          <BookOpen className="w-5 h-5 text-sky-600 flex-shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <span className="font-bold uppercase tracking-wider text-[11px] text-sky-800">
              Returning Patient Memory Notice
            </span>
            <p>
              Patient previously visited on <strong>{returning_patient_context.previous_routing_date}</strong> and was routed to <strong>{returning_patient_context.previous_department}</strong>.
              Today's current assessment was evaluated independently for fresh clinical symptoms.
            </p>
          </div>
        </div>
      )}

      {/* Main Department Decision Card */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-6">
          <div className="space-y-1">
            <span className="text-xs font-bold text-sky-700 uppercase tracking-wider">
              Assigned Clinical Department
            </span>
            <div className="flex items-center space-x-3">
              <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
                {selected_department}
              </h2>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-sky-100 text-sky-800 border border-sky-200">
                {department_code}
              </span>
            </div>
          </div>

          {/* Confidence Badge */}
          <div className="flex items-center space-x-3 bg-slate-50 border border-slate-200 px-4 py-2.5 rounded-2xl w-fit">
            <div className="text-right">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Routing Confidence</p>
              <p className="text-base font-extrabold text-slate-900">{confidencePercentage}% Match</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-teal-500/10 text-teal-600 flex items-center justify-center font-bold text-xs">
              <Sparkles className="w-5 h-5" />
            </div>
          </div>
        </div>

        {/* Clinical Routing Rationale */}
        <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200 space-y-2">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5">
            <Compass className="w-4 h-4 text-sky-600" />
            <span>Triage Routing Rationale</span>
          </span>
          <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">
            {routing_reason}
          </p>
          {alternative_department && (
            <p className="text-xs text-slate-500 pt-1">
              <strong>Differential Assessment:</strong> If secondary symptoms present, consider cross-consult with {alternative_department}.
            </p>
          )}
        </div>

        {/* Intake Summary Details */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-slate-400 block mb-0.5 font-medium">Patient</span>
            <span className="font-bold text-slate-800">{patient_name} (Age: {age})</span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-slate-400 block mb-0.5 font-medium">Session ID</span>
            <span className="font-mono font-bold text-slate-800">{result.session_id}</span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-slate-400 block mb-0.5 font-medium">Patient ID</span>
            <span className="font-mono font-bold text-slate-800">{patient_id}</span>
          </div>
        </div>
      </div>

      {/* RAG-Grounded Department Instructions & Requirements */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Required Documents */}
        <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
            <FileCheck className="w-5 h-5 text-teal-600" />
            <h3 className="font-bold text-slate-900 text-base">Documents to Bring</h3>
          </div>

          <ul className="space-y-2.5 text-xs text-slate-700">
            {documents_required.map((doc, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <CheckCircle2 className="w-4 h-4 text-teal-600 flex-shrink-0 mt-0.5" />
                <span className="leading-relaxed">{doc}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Preparation Guidelines */}
        <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
            <Calendar className="w-5 h-5 text-sky-600" />
            <h3 className="font-bold text-slate-900 text-base">Preparation Instructions</h3>
          </div>

          <ul className="space-y-2.5 text-xs text-slate-700">
            {preparation_instructions.map((prep, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <CheckCircle2 className="w-4 h-4 text-sky-600 flex-shrink-0 mt-0.5" />
                <span className="leading-relaxed">{prep}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Department Intake Instructions */}
      {intake_instructions && (
        <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-3">
          <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
            <Building2 className="w-5 h-5 text-sky-600" />
            <h3 className="font-bold text-slate-900 text-base">Department Intake &amp; Check-In Protocol</h3>
          </div>
          <div className="text-xs text-slate-700 whitespace-pre-line leading-relaxed">
            {intake_instructions}
          </div>
        </div>
      )}

      {/* ChromaDB RAG Grounded Document References */}
      {source_references.length > 0 && (
        <div className="bg-slate-50 rounded-3xl border border-slate-200 p-6 space-y-3">
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-slate-600" />
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Grounded Document References (ChromaDB RAG)
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {source_references.map((ref, idx) => (
              <div key={idx} className="bg-white p-3.5 rounded-xl border border-slate-200 text-xs space-y-1">
                <div className="flex items-center justify-between text-[11px] font-bold text-sky-800">
                  <span>{ref.document_name}</span>
                  <span className="text-slate-400 font-normal">{ref.section}</span>
                </div>
                <p className="text-slate-600 italic text-[11px] leading-relaxed">
                  "{ref.snippet}"
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action CTA: Move to Appointment Scheduling */}
      <div className="flex justify-end pt-2">
        <button
          onClick={onProceedToBooking}
          className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-sky-600 to-teal-600 hover:from-sky-500 hover:to-teal-500 text-white font-bold text-sm shadow-md flex items-center space-x-2 transition-all cursor-pointer"
        >
          <span>Select Available Appointment Slot</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
