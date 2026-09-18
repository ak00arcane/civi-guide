"use client";

import React, { useState, useEffect } from "react";
import { ClarifyingQuestion } from "@/lib/api";

interface ProfileWizardProps {
  isOpen: boolean;
  onClose: () => void;
  initialFields?: Record<string, any>;
  clarifyingQuestions?: ClarifyingQuestion[];
  onSaveProfile: (fields: Record<string, any>) => void;
}

export const ProfileWizard: React.FC<ProfileWizardProps> = ({
  isOpen,
  onClose,
  initialFields = {},
  clarifyingQuestions = [],
  onSaveProfile,
}) => {
  const [fields, setFields] = useState<Record<string, any>>({
    age: "",
    state: "",
    district: "",
    annual_family_income: "",
    education: "",
    occupation: "",
    employment_status: "",
    gender: "",
    disability_status: "",
    farmer_status: "",
    business_status: "",
  });

  useEffect(() => {
    if (initialFields) {
      setFields((prev) => ({
        ...prev,
        ...Object.fromEntries(Object.entries(initialFields).map(([k, v]) => [k, v ?? ""])),
      }));
    }
  }, [initialFields]);

  if (!isOpen) return null;

  const handleChange = (key: string, value: any) => {
    setFields((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const sanitized: Record<string, any> = {};
    Object.entries(fields).forEach(([k, v]) => {
      if (v === "" || v === null || v === undefined) {
        sanitized[k] = null;
      } else if (k === "age" || k === "annual_family_income") {
        const num = Number(v);
        sanitized[k] = isNaN(num) ? null : num;
      } else {
        sanitized[k] = v;
      }
    });
    onSaveProfile(sanitized);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-[2px] overflow-y-auto">
      <div className="w-full max-w-2xl bg-white border border-[var(--border-color)] rounded-2xl shadow-[var(--shadow-lg)] my-8">
        <div className="flex items-start justify-between px-6 pt-6 pb-4 border-b border-[var(--border-color)]">
          <div>
            <h2 className="text-lg font-bold text-[var(--text-main)]">Your Profile</h2>
            <p className="text-xs text-[var(--text-muted)] mt-1">
              Optional details that improve match accuracy — you can skip any field.
            </p>
          </div>
          <button onClick={onClose} className="btn btn-ghost w-8 h-8 p-0 text-sm">
            ✕
          </button>
        </div>

        <div className="px-6 py-5 space-y-6 max-h-[70vh] overflow-y-auto">
          {clarifyingQuestions && clarifyingQuestions.length > 0 && (
            <div className="bg-[var(--primary-soft-bg)] border border-[var(--primary-soft-border)] rounded-xl p-4 space-y-3">
              <span className="text-xs font-bold text-[var(--primary)] uppercase tracking-wide">
                Clarifying Questions
              </span>
              {clarifyingQuestions.map((q, idx) => (
                <div key={idx} className="space-y-2">
                  <p className="text-sm font-medium text-[var(--text-main)]">{q.prompt}</p>
                  {q.options && (
                    <div className="flex flex-wrap gap-2">
                      {q.options.map((opt, oIdx) => (
                        <button
                          key={oIdx}
                          type="button"
                          onClick={() => handleChange(q.field, opt.value)}
                          className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-colors ${
                            fields[q.field] === opt.value
                              ? "bg-[var(--primary)] text-white border-[var(--primary)]"
                              : "bg-white text-[var(--text-muted)] border-[var(--border-strong)] hover:border-[var(--primary)]"
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          <form id="profile-form" onSubmit={handleSubmit} className="space-y-6">
            {/* About you */}
            <fieldset className="space-y-3">
              <legend className="text-xs font-bold text-[var(--text-dim)] uppercase tracking-wide mb-1">
                About you
              </legend>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div>
                  <label className="field-label">Age (years)</label>
                  <input
                    type="number"
                    value={fields.age}
                    onChange={(e) => handleChange("age", e.target.value)}
                    placeholder="e.g. 24"
                    className="field-input"
                  />
                </div>
                <div>
                  <label className="field-label">Gender</label>
                  <select
                    value={fields.gender}
                    onChange={(e) => handleChange("gender", e.target.value)}
                    className="field-input"
                  >
                    <option value="">Not specified</option>
                    <option value="female">Female</option>
                    <option value="male">Male</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
            </fieldset>

            {/* Location */}
            <fieldset className="space-y-3">
              <legend className="text-xs font-bold text-[var(--text-dim)] uppercase tracking-wide mb-1">
                Location
              </legend>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div>
                  <label className="field-label">State / Union Territory</label>
                  <input
                    type="text"
                    value={fields.state}
                    onChange={(e) => handleChange("state", e.target.value)}
                    placeholder="e.g. Tamil Nadu"
                    className="field-input"
                  />
                </div>
                <div>
                  <label className="field-label">District</label>
                  <input
                    type="text"
                    value={fields.district}
                    onChange={(e) => handleChange("district", e.target.value)}
                    placeholder="e.g. Chennai"
                    className="field-input"
                  />
                </div>
              </div>
            </fieldset>

            {/* Financial & status */}
            <fieldset className="space-y-3">
              <legend className="text-xs font-bold text-[var(--text-dim)] uppercase tracking-wide mb-1">
                Financial &amp; status
              </legend>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div>
                  <label className="field-label">Annual family income (₹)</label>
                  <input
                    type="number"
                    value={fields.annual_family_income}
                    onChange={(e) => handleChange("annual_family_income", e.target.value)}
                    placeholder="e.g. 250000"
                    className="field-input"
                  />
                </div>
                <div>
                  <label className="field-label">Education level</label>
                  <select
                    value={fields.education}
                    onChange={(e) => handleChange("education", e.target.value)}
                    className="field-input"
                  >
                    <option value="">Not specified</option>
                    <option value="Student">Secondary / Student</option>
                    <option value="Class 12">Class 12</option>
                    <option value="Graduate">Graduate</option>
                    <option value="Engineering">Engineering</option>
                  </select>
                </div>
                <div>
                  <label className="field-label">Employment status</label>
                  <select
                    value={fields.employment_status}
                    onChange={(e) => handleChange("employment_status", e.target.value)}
                    className="field-input"
                  >
                    <option value="">Not specified</option>
                    <option value="unemployed">Unemployed</option>
                    <option value="job_seeker">Job seeker</option>
                    <option value="self_employed">Self-employed / entrepreneur</option>
                    <option value="student">Student</option>
                    <option value="farmer">Farmer</option>
                  </select>
                </div>
                <div>
                  <label className="field-label">Person with disability (PwD)</label>
                  <select
                    value={fields.disability_status}
                    onChange={(e) => handleChange("disability_status", e.target.value)}
                    className="field-input"
                  >
                    <option value="">No / unknown</option>
                    <option value="yes">Yes</option>
                  </select>
                </div>
              </div>
            </fieldset>
          </form>
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-[var(--border-color)]">
          <button type="button" onClick={onClose} className="btn btn-secondary text-sm px-4 py-2">
            Cancel
          </button>
          <button type="submit" form="profile-form" className="btn btn-primary text-sm px-5 py-2">
            Update Recommendations
          </button>
        </div>
      </div>
    </div>
  );
};
