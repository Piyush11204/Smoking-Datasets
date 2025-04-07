import React, { useState } from 'react';

function Home() {
  const [formData, setFormData] = useState({
    gender: 'Male',
    age: '21',
    years_smoking: '5',
    cigarettes_per_day: '4',
    previous_attempts: '3',
    craving_level: '4',
    stress_level: '5',
    physical_activity: '3',
    support_system: '2',
    nicotine_dependence: '4',
    reason_for_starting: 'Curiosity'
  });

  const [status, setStatus] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('Generating report...');

    try {
      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...formData,
          age: Number(formData.age),
          years_smoking: Number(formData.years_smoking),
          cigarettes_per_day: Number(formData.cigarettes_per_day),
          previous_attempts: Number(formData.previous_attempts),
          craving_level: Number(formData.craving_level),
          stress_level: Number(formData.stress_level),
          physical_activity: Number(formData.physical_activity),
          support_system: Number(formData.support_system),
          nicotine_dependence: Number(formData.nicotine_dependence)
        })
      });

      const result = await response.json();
      const report = result.report || JSON.stringify(result, null, 2);

      const blob = new Blob([report], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'smoking_report.txt';
      a.click();
      URL.revokeObjectURL(url);

      setStatus('Report downloaded successfully!');
    } catch (error) {
      console.error(error);
      setStatus('Failed to generate report.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-center mb-6">Smoking Cessation Report Generator</h1>

      <form onSubmit={handleSubmit} className="space-y-4 bg-white shadow p-6 rounded-xl">
        <div className="grid md:grid-cols-2 gap-4">
          <input type="text" name="age" placeholder="Age" value={formData.age} onChange={handleChange} className="border p-2 rounded w-full" required />
          <input type="text" name="years_smoking" placeholder="Years Smoking" value={formData.years_smoking} onChange={handleChange} className="border p-2 rounded w-full" required />
          <input type="text" name="cigarettes_per_day" placeholder="Cigarettes Per Day" value={formData.cigarettes_per_day} onChange={handleChange} className="border p-2 rounded w-full" required />
          <input type="text" name="previous_attempts" placeholder="Previous Attempts" value={formData.previous_attempts} onChange={handleChange} className="border p-2 rounded w-full" required />
          <input type="text" name="craving_level" placeholder="Craving Level (1-10)" value={formData.craving_level} onChange={handleChange} className="border p-2 rounded w-full" required />
          <input type="text" name="stress_level" placeholder="Stress Level (1-10)" value={formData.stress_level} onChange={handleChange} className="border p-2 rounded w-full" required />
          <input type="text" name="physical_activity" placeholder="Physical Activity (1-10)" value={formData.physical_activity} onChange={handleChange} className="border p-2 rounded w-full" required />
          <input type="text" name="support_system" placeholder="Support System (1-10)" value={formData.support_system} onChange={handleChange} className="border p-2 rounded w-full" required />
          <input type="text" name="nicotine_dependence" placeholder="Nicotine Dependence (1-10)" value={formData.nicotine_dependence} onChange={handleChange} className="border p-2 rounded w-full" required />
          <input type="text" name="reason_for_starting" placeholder="Reason for Starting" value={formData.reason_for_starting} onChange={handleChange} className="border p-2 rounded w-full" required />
        </div>

        <button type="submit" className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 w-full">
          Generate & Download Report
        </button>
        <div className="text-center text-sm mt-2 text-gray-700">{status}</div>
      </form>
    </div>
  );
}

export default Home;
