import React from "react";

export default function RecruiterDashboard() {
  return (
    <main className="p-8 max-w-5xl mx-auto font-sans">
      <h1 className="text-3xl font-bold mb-2">Automated Resume Screening Dashboard</h1>
      <p className="text-gray-600 mb-6">Rank candidates by JD similarity, must-have skill coverage, and experience.</p>
      <div className="border rounded-lg p-4 bg-white shadow-sm">
        <p className="text-sm text-gray-500">Connect to FastAPI backend at <code>POST /rank</code> to score uploaded resumes.</p>
      </div>
    </main>
  );
}
