import React, { useState } from 'react';
import Navbar from './components/Navbar';
import HomeDashboard from './components/HomeDashboard';
import PatientIntakeForm from './components/PatientIntakeForm';
import AgentTracker from './components/AgentTracker';
import RoutingResults from './components/RoutingResults';
import AppointmentBooking from './components/AppointmentBooking';
import UrgentCareScreen from './components/UrgentCareScreen';
import AdminDashboard from './components/AdminDashboard';
import AgentRosterView from './components/AgentRosterView';
import ReturningPatientHistory from './components/ReturningPatientHistory';
import api from './services/api';
import { AlertCircle, RotateCcw } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [isLoading, setIsLoading] = useState(false);
  const [routingResult, setRoutingResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleStartIntake = () => {
    setRoutingResult(null);
    setErrorMessage(null);
    setActiveTab('intake');
  };

  const handleIntakeSubmit = async (formData) => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const res = await api.processIntake(formData);
      setRoutingResult(res);

      if (res.is_urgent) {
        setActiveTab('urgent');
      } else {
        setActiveTab('results');
      }
    } catch (err) {
      console.error('Error during intake orchestration:', err);
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : (detail?.errors?.join(', ') || 'Failed to process intake.');
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setRoutingResult(null);
    setErrorMessage(null);
    setActiveTab('intake');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-16">
        {/* Error notification banner */}
        {errorMessage && (
          <div className="mb-6 p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-slate-400 hover:text-slate-600 font-bold"
            >
              ✕
            </button>
          </div>
        )}

        {/* Tab 1: Home Dashboard */}
        {activeTab === 'home' && (
          <HomeDashboard onStartIntake={handleStartIntake} />
        )}

        {/* Tab 2: Patient Intake Form */}
        {activeTab === 'intake' && (
          <div className="space-y-10">
            <PatientIntakeForm onSubmit={handleIntakeSubmit} isLoading={isLoading} />
            <ReturningPatientHistory
              patientId="P-1001"
              onStartNew={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            />
          </div>
        )}

        {/* Tab 3: Routing Results Screen */}
        {activeTab === 'results' && routingResult && (
          <div className="space-y-8 animate-in fade-in">
            <AgentTracker traces={routingResult.agent_traces} isRunning={isLoading} />
            <RoutingResults
              result={routingResult}
              onProceedToBooking={() => setActiveTab('booking')}
            />
          </div>
        )}

        {/* Tab 4: Appointment Booking Screen */}
        {activeTab === 'booking' && routingResult && (
          <div className="space-y-8 animate-in fade-in">
            <AppointmentBooking
              departmentCode={routingResult.department_code}
              departmentName={routingResult.selected_department}
              patientId={routingResult.patient_id}
              patientName={routingResult.patient_name}
              onNewIntake={handleReset}
            />
          </div>
        )}

        {/* Tab 5: Urgent Care Emergency Screen */}
        {activeTab === 'urgent' && routingResult && (
          <div className="space-y-8 animate-in fade-in">
            <AgentTracker traces={routingResult.agent_traces} isRunning={false} />
            <UrgentCareScreen
              result={routingResult}
              onRestart={handleReset}
            />
          </div>
        )}

        {/* Tab 6: Agent Roster Capabilities */}
        {activeTab === 'agents' && (
          <AgentRosterView />
        )}

        {/* Tab 7: Admin Console */}
        {activeTab === 'admin' && (
          <AdminDashboard />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 space-y-1">
          <p className="font-semibold text-slate-700">
            CareRoute AI • Hospital Patient Intake &amp; Department Routing Assistant
          </p>
          <p className="text-[11px] text-slate-400">
            Multi-Agent Architecture powered by Microsoft Semantic Kernel • ChromaDB RAG Engine • SQLite Database
          </p>
        </div>
      </footer>
    </div>
  );
}
