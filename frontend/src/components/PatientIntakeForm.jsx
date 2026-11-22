import React, { useState } from 'react';
import {
  User,
  Calendar,
  AlertCircle,
  Clock,
  FileEdit,
  Send,
  Sparkles,
  RefreshCw,
  Info
} from 'lucide-react';

export default function PatientIntakeForm({ onSubmit, isLoading }) {
  const [formData, setFormData] = useState({
    patient_name: '',
    age: '',
    described_concern: '',
    duration: '',
    additional_info: '',
    is_returning_patient: false,
    patient_id: ''
  });

  const [errors, setErrors] = useState({});

  const presetScenarios = [
    {
      label: 'Scenario 1: Knee Pain',
      desc: 'Orthopaedics Routing',
      data: {
        patient_name: 'Arthur Pendelton',
        age: 48,
        described_concern: 'I have severe right knee pain for three days after stepping off a curb awkwardly. Swelling and difficulty bending the knee.',
        duration: '3 days',
        additional_info: 'No previous knee surgery. Taking ibuprofen with partial relief.',
        is_returning_patient: false,
        patient_id: ''
      }
    },
    {
      label: 'Scenario 2: Emergency Chest Pain',
      desc: 'Safety Gate Stop',
      badge: 'Urgent',
      data: {
        patient_name: 'Sarah Connor',
        age: 56,
        described_concern: 'I have severe chest pain and difficulty breathing that started suddenly 45 minutes ago. Heavy crushing sensation radiating to my left shoulder.',
        duration: '45 minutes',
        additional_info: 'Cold sweats and dizziness. Known history of hypertension.',
        is_returning_patient: false,
        patient_id: ''
      }
    },
    {
      label: 'Scenario 3: Returning Patient',
      desc: 'Memory Recall (P-1001)',
      data: {
        patient_name: 'Eleanor Vance',
        age: 45,
        described_concern: 'Developing an intensely itchy red rash with small bumps across both forearms after applying a new moisturizer.',
        duration: '4 days',
        additional_info: 'Visited hospital 3 weeks ago for knee osteoarthritis. No known drug allergies.',
        is_returning_patient: true,
        patient_id: 'P-1001'
      }
    },
    {
      label: 'Ambiguous: Generalized Fatigue',
      desc: 'General Medicine Fallback',
      data: {
        patient_name: 'David Miller',
        age: 39,
        described_concern: 'Feeling constantly tired, sluggish, and generally unwell for the past two weeks without specific pain anywhere.',
        duration: '2 weeks',
        additional_info: 'Appetite slightly decreased. Non-smoker.',
        is_returning_patient: false,
        patient_id: ''
      }
    }
  ];

  const applyPreset = (preset) => {
    setFormData(preset.data);
    setErrors({});
  };

  const validate = () => {
    const errs = {};
    if (!formData.patient_name.trim() || formData.patient_name.trim().length < 2) {
      errs.patient_name = 'Patient name must be at least 2 characters.';
    }
    const ageNum = parseInt(formData.age, 10);
    if (isNaN(ageNum) || ageNum < 0 || ageNum > 120) {
      errs.age = 'Age must be a valid number between 0 and 120.';
    }
    if (!formData.described_concern.trim() || formData.described_concern.trim().length < 5) {
      errs.described_concern = 'Please provide a clear description of symptoms (minimum 5 characters).';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;

    onSubmit({
      ...formData,
      age: parseInt(formData.age, 10),
      duration: formData.duration.trim() || 'Unspecified',
      additional_info: formData.additional_info.trim() || '',
      patient_id: formData.patient_id.trim() || undefined
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">Patient Intake Form</h2>
        <p className="text-sm text-slate-600 max-w-xl mx-auto">
          Please describe the patient's symptoms and details. Our multi-agent system will validate,
          check medical safety rules, and route to the correct hospital department.
        </p>
      </div>

      {/* Quick Demo Scenario Presets */}
      <div className="bg-gradient-to-r from-sky-50 to-teal-50 border border-sky-200/80 rounded-2xl p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-sky-900 uppercase tracking-wider flex items-center space-x-1.5">
            <Sparkles className="w-4 h-4 text-sky-600" />
            <span>Fast Demo Presets (Click to autofill)</span>
          </span>
          <span className="text-xs text-sky-700 font-medium">Testing shortcuts</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {presetScenarios.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => applyPreset(preset)}
              className="text-left p-3 rounded-xl bg-white border border-slate-200 hover:border-sky-400 hover:shadow transition-all group cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <p className="text-xs font-bold text-slate-800 group-hover:text-sky-700">{preset.label}</p>
                {preset.badge && (
                  <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-rose-100 text-rose-700">
                    {preset.badge}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">{preset.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Main Intake Form Card */}
      <form onSubmit={handleSubmit} className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {/* Patient Name */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
              Patient Full Name or Identifier *
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                placeholder="e.g. John Doe / P-1001"
                value={formData.patient_name}
                onChange={(e) => setFormData({ ...formData, patient_name: e.target.value })}
                className={`w-full pl-10 pr-4 py-2.5 rounded-xl border text-sm text-slate-900 focus:outline-none focus:ring-2 transition-all ${
                  errors.patient_name
                    ? 'border-rose-400 focus:ring-rose-200'
                    : 'border-slate-300 focus:border-sky-500 focus:ring-sky-100'
                }`}
              />
            </div>
            {errors.patient_name && (
              <p className="text-xs text-rose-600 flex items-center space-x-1">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>{errors.patient_name}</span>
              </p>
            )}
          </div>

          {/* Patient Age */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
              Age (Years) *
            </label>
            <div className="relative">
              <Calendar className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="number"
                min="0"
                max="120"
                placeholder="e.g. 42 (Minors &lt; 18 route to Paediatrics)"
                value={formData.age}
                onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                className={`w-full pl-10 pr-4 py-2.5 rounded-xl border text-sm text-slate-900 focus:outline-none focus:ring-2 transition-all ${
                  errors.age
                    ? 'border-rose-400 focus:ring-rose-200'
                    : 'border-slate-300 focus:border-sky-500 focus:ring-sky-100'
                }`}
              />
            </div>
            {errors.age && (
              <p className="text-xs text-rose-600 flex items-center space-x-1">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>{errors.age}</span>
              </p>
            )}
          </div>
        </div>

        {/* Described Medical Concern */}
        <div className="space-y-1.5">
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between">
            <span>Patient's Described Concern &amp; Symptoms *</span>
            <span className="text-[11px] font-normal text-slate-500">Be as descriptive as possible</span>
          </label>
          <textarea
            rows="4"
            placeholder="Describe what symptoms the patient is experiencing (e.g. knee pain, persistent cough, skin rash, etc.)..."
            value={formData.described_concern}
            onChange={(e) => setFormData({ ...formData, described_concern: e.target.value })}
            className={`w-full p-3.5 rounded-xl border text-sm text-slate-900 focus:outline-none focus:ring-2 transition-all ${
              errors.described_concern
                ? 'border-rose-400 focus:ring-rose-200'
                : 'border-slate-300 focus:border-sky-500 focus:ring-sky-100'
            }`}
          />
          {errors.described_concern && (
            <p className="text-xs text-rose-600 flex items-center space-x-1">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>{errors.described_concern}</span>
            </p>
          )}
        </div>

        {/* Duration & Returning Patient Details */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {/* Duration */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
              Duration of Symptoms
            </label>
            <div className="relative">
              <Clock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                placeholder="e.g. 3 days, 2 weeks, sudden onset"
                value={formData.duration}
                onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 focus:border-sky-500 focus:ring-2 focus:ring-sky-100 text-sm text-slate-900 focus:outline-none"
              />
            </div>
          </div>

          {/* Returning Patient Toggle */}
          <div className="space-y-2">
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
              Returning Patient Status
            </label>
            <div className="flex items-center space-x-3 pt-1.5">
              <label className="flex items-center space-x-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_returning_patient}
                  onChange={(e) => setFormData({ ...formData, is_returning_patient: e.target.checked })}
                  className="w-4 h-4 text-sky-600 rounded border-slate-300 focus:ring-sky-500"
                />
                <span className="text-xs font-semibold text-slate-800">Returning patient with prior visit history</span>
              </label>
            </div>
            {formData.is_returning_patient && (
              <input
                type="text"
                placeholder="Existing Patient ID (optional, e.g. P-1001)"
                value={formData.patient_id}
                onChange={(e) => setFormData({ ...formData, patient_id: e.target.value })}
                className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-sky-500 mt-1"
              />
            )}
          </div>
        </div>

        {/* Additional Clinical Context */}
        <div className="space-y-1.5">
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
            Additional Clinical Details (Optional)
          </label>
          <input
            type="text"
            placeholder="e.g. History of asthma, current medications, specific triggers, etc."
            value={formData.additional_info}
            onChange={(e) => setFormData({ ...formData, additional_info: e.target.value })}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:border-sky-500 focus:ring-2 focus:ring-sky-100 text-sm text-slate-900 focus:outline-none"
          />
        </div>

        {/* Submit Button */}
        <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
          <div className="flex items-center space-x-1.5 text-xs text-slate-500">
            <Info className="w-4 h-4 text-sky-500" />
            <span>Executes all 6 Semantic Kernel agents</span>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-sky-600 to-teal-600 hover:from-sky-500 hover:to-teal-500 text-white font-bold text-sm shadow-md shadow-sky-600/20 flex items-center space-x-2 transition-all disabled:opacity-50 cursor-pointer"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Orchestrating Agents...</span>
              </>
            ) : (
              <>
                <span>Submit For Triage Routing</span>
                <Send className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
