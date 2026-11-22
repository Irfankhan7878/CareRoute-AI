import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  UserCheck,
  CheckCircle2,
  AlertCircle,
  Building2,
  ShieldCheck,
  RefreshCw,
  Sparkles,
  Ticket
} from 'lucide-react';
import api from '../services/api';

export default function AppointmentBooking({ departmentCode, departmentName, patientId, patientName, onNewIntake }) {
  const [slots, setSlots] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(true);
  const [selectedSlotId, setSelectedSlotId] = useState(null);
  const [isBooking, setIsBooking] = useState(false);
  const [bookingSuccess, setBookingSuccess] = useState(null);
  const [bookingError, setBookingError] = useState(null);

  useEffect(() => {
    if (!departmentCode) return;
    setLoadingSlots(true);
    api.getAvailableAppointments(departmentCode)
      .then(data => setSlots(data))
      .catch(err => console.error('Error loading slots:', err))
      .finally(() => setLoadingSlots(false));
  }, [departmentCode]);

  const handleBook = async () => {
    if (!selectedSlotId) return;
    setIsBooking(true);
    setBookingError(null);

    try {
      const res = await api.bookAppointment(selectedSlotId, patientId, patientName);
      setBookingSuccess(res);
      // Remove booked slot from list
      setSlots(slots.filter(s => s.id !== selectedSlotId));
      setSelectedSlotId(null);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to book slot.';
      setBookingError(msg);
    } finally {
      setIsBooking(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Demonstration Appointment Scheduling
        </h2>
        <p className="text-sm text-slate-600 max-w-xl mx-auto">
          Reserve an available consultation slot for <strong>{departmentName}</strong> ({departmentCode}).
        </p>
      </div>

      {/* Demo Notification Notice */}
      <div className="bg-sky-50 border border-sky-200 rounded-2xl p-4 flex items-center space-x-3 text-sky-900 text-xs">
        <ShieldCheck className="w-5 h-5 text-sky-600 flex-shrink-0" />
        <span>
          <strong>DEMONSTRATION BOOKINGS ONLY:</strong> These appointment slots are synthetic records stored in the SQLite database to demonstrate real-time slot conflict prevention. No actual clinic booking is created.
        </span>
      </div>

      {/* Successful Booking Confirmation Card */}
      {bookingSuccess && (
        <div className="bg-emerald-50 border-2 border-emerald-400 rounded-3xl p-6 sm:p-8 shadow-sm space-y-4 animate-in fade-in">
          <div className="flex items-center space-x-3 text-emerald-800">
            <CheckCircle2 className="w-8 h-8 text-emerald-600 flex-shrink-0" />
            <div>
              <h3 className="text-xl font-bold">Appointment Confirmed Successfully!</h3>
              <p className="text-xs text-emerald-700">Atomic database reservation completed with unique reference ID.</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-emerald-200 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-slate-400 block mb-0.5">Booking Reference</span>
              <span className="font-mono font-bold text-emerald-700 text-sm">{bookingSuccess.booking_reference}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">Date &amp; Time</span>
              <span className="font-bold text-slate-800">{bookingSuccess.appointment_date} at {bookingSuccess.time_slot}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">Assigned Clinician</span>
              <span className="font-bold text-slate-800">{bookingSuccess.doctor_name}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">Department</span>
              <span className="font-bold text-slate-800">{bookingSuccess.department_name}</span>
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              onClick={onNewIntake}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-sm transition-all cursor-pointer"
            >
              Start New Patient Intake
            </button>
          </div>
        </div>
      )}

      {/* Available Slots Grid */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h3 className="font-bold text-slate-900 text-lg">Available Consultation Slots</h3>
            <p className="text-xs text-slate-500">Select a date and time slot below to reserve</p>
          </div>
          <span className="text-xs font-semibold px-3 py-1 bg-slate-100 text-slate-700 rounded-full">
            {slots.length} Slots Available
          </span>
        </div>

        {bookingError && (
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 text-xs text-rose-800 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{bookingError}</span>
          </div>
        )}

        {loadingSlots ? (
          <div className="py-12 text-center text-slate-400 flex flex-col items-center space-y-2">
            <RefreshCw className="w-6 h-6 animate-spin text-sky-600" />
            <span className="text-xs">Loading available slots from database...</span>
          </div>
        ) : slots.length === 0 ? (
          <div className="py-12 text-center text-slate-500 space-y-2">
            <Calendar className="w-8 h-8 text-slate-300 mx-auto" />
            <p className="text-sm font-semibold">No appointment slots currently available for this department.</p>
            <p className="text-xs text-slate-400">Please check back later or proceed via walk-in intake.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {slots.map((slot) => {
              const isSelected = selectedSlotId === slot.id;
              return (
                <div
                  key={slot.id}
                  onClick={() => setSelectedSlotId(slot.id)}
                  className={`p-4 rounded-2xl border text-left cursor-pointer transition-all ${
                    isSelected
                      ? 'border-sky-600 bg-sky-50/60 ring-2 ring-sky-500/20 shadow-sm'
                      : 'border-slate-200 hover:border-sky-300 hover:bg-slate-50/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
                      <Clock className="w-3.5 h-3.5 text-sky-600" />
                      <span>{slot.time_slot}</span>
                    </span>
                    <span className="text-[10px] font-semibold text-slate-500 px-2 py-0.5 rounded bg-slate-100">
                      {slot.date}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 truncate mb-2">
                    {slot.doctor_name}
                  </p>

                  <div className="flex items-center justify-between text-[11px] pt-1.5 border-t border-slate-100">
                    <span className="text-emerald-700 font-semibold text-[10px] bg-emerald-50 px-1.5 py-0.5 rounded">
                      Available
                    </span>
                    <span className={`text-[11px] font-bold ${isSelected ? 'text-sky-700' : 'text-slate-400'}`}>
                      {isSelected ? '✓ Selected' : 'Click to select'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Action Button */}
        {slots.length > 0 && (
          <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
            <div className="text-xs text-slate-500">
              Patient: <strong>{patientName}</strong> ({patientId})
            </div>

            <button
              onClick={handleBook}
              disabled={!selectedSlotId || isBooking}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-sky-600 to-teal-600 hover:from-sky-500 hover:to-teal-500 text-white font-bold text-sm shadow-md transition-all disabled:opacity-40 cursor-pointer flex items-center space-x-2"
            >
              {isBooking ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Reserving Slot...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Confirm Appointment Reservation</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
