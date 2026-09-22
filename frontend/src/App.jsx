import { useState, useEffect, useMemo } from 'react';
import { Activity, Network, ShieldCheck, ServerCrash, Play, AlertCircle, Brain, LayoutDashboard, Info, ArrowRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

function App() {
  const [backendStatus, setBackendStatus] = useState('Checking...');
  const [flows, setFlows] = useState([]);
  const [flowCount, setFlowCount] = useState(100);
  const [loading, setLoading] = useState(false);
  const [classifying, setClassifying] = useState(false);
  const [error, setError] = useState(null);
  
  const [predictions, setPredictions] = useState(null);
  const [mlMetrics, setMlMetrics] = useState(null);
  
  const [serviceCapacity, setServiceCapacity] = useState(1000);
  const [simulating, setSimulating] = useState(false);
  const [simulationResults, setSimulationResults] = useState(null);

  useEffect(() => {
    const checkBackendHealth = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/health');
        if (response.ok) {
          setBackendStatus('Connected');
        } else {
          setBackendStatus('Disconnected');
        }
      } catch (err) {
        setBackendStatus('Disconnected');
      }
    };
    checkBackendHealth();
  }, []);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setPredictions(null);
    setSimulationResults(null);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/traffic/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: parseInt(flowCount) })
      });
      if (!response.ok) {
        throw new Error('Unable to connect to the simulation API or failed to generate traffic.');
      }
      const data = await response.json();
      setFlows(data.flows);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const handleClassify = async () => {
    setClassifying(true);
    setError(null);
    setSimulationResults(null);
    try {
      if (!mlMetrics) {
        const metricsRes = await fetch('http://127.0.0.1:8000/api/ml/metrics');
        if (metricsRes.ok) {
          setMlMetrics(await metricsRes.json());
        }
      }
      
      const response = await fetch('http://127.0.0.1:8000/api/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flows })
      });
      if (!response.ok) {
        throw new Error('Unable to connect to the simulation API or failed to classify traffic.');
      }
      const data = await response.json();
      
      const predMap = {};
      data.results.forEach(r => {
        predMap[r.flowId] = r;
      });
      setPredictions(predMap);
    } catch (err) {
      setError(err.message);
    } finally {
      setClassifying(false);
    }
  };

  const handleSimulate = async () => {
    setSimulating(true);
    setError(null);
    try {
      const payloadFlows = flows.map((f, idx) => {
        const pred = predictions[f.flowId];
        return {
          flowId: f.flowId,
          trafficClass: pred.predictedClass,
          priority: pred.priority,
          packetCount: f.packetCount,
          averagePacketSize: f.averagePacketSize,
          arrivalOrder: idx
        };
      });

      const response = await fetch('http://127.0.0.1:8000/api/metrics/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          flows: payloadFlows,
          serviceCapacity: parseInt(serviceCapacity)
        })
      });
      
      if (!response.ok) {
        throw new Error('Unable to connect to the simulation API or failed to run simulation.');
      }
      const data = await response.json();
      setSimulationResults(data);
    } catch(err) {
      setError(err.message);
    } finally {
      setSimulating(false);
    }
  };

  const stats = useMemo(() => {
    if (!flows.length) return null;
    const tcp = flows.filter(f => f.protocol === 'TCP').length;
    const udp = flows.filter(f => f.protocol === 'UDP').length;
    const avgSize = flows.reduce((acc, f) => acc + f.averagePacketSize, 0) / flows.length;
    const totalPackets = flows.reduce((acc, f) => acc + f.packetCount, 0);
    return { tcp, udp, avgSize: avgSize.toFixed(0), totalPackets };
  }, [flows]);

  const protocolDistribution = useMemo(() => {
    if (!flows.length) return [];
    const counts = { TCP: 0, UDP: 0 };
    flows.forEach(f => { counts[f.protocol] = (counts[f.protocol] || 0) + 1; });
    return [
      { name: 'TCP', value: counts.TCP },
      { name: 'UDP', value: counts.UDP }
    ];
  }, [flows]);

  const priorityDistribution = useMemo(() => {
    if (!predictions || !Object.keys(predictions).length) return [];
    const counts = { Critical: 0, High: 0, Medium: 0, Low: 0 };
    Object.values(predictions).forEach(p => {
      if (counts[p.priority] !== undefined) {
        counts[p.priority] += 1;
      }
    });
    return [
      { name: 'Critical', value: counts.Critical },
      { name: 'High', value: counts.High },
      { name: 'Medium', value: counts.Medium },
      { name: 'Low', value: counts.Low }
    ];
  }, [predictions]);

  const simulationInsights = useMemo(() => {
    if (!simulationResults) return [];
    const insights = [];
    
    insights.push("AI-Priority provides preferential service to higher-priority traffic.");
    
    if (simulationResults.fifo.throughputMbps === simulationResults.priority.throughputMbps) {
      insights.push("Throughput is unchanged between the two strategies under this simulated workload.");
    }
    
    if (simulationResults.priority.averageQueueLatency > simulationResults.fifo.averageQueueLatency) {
      insights.push("AI-Priority produces higher overall average queue latency in this scenario because lower-priority flows suffer extreme wait times.");
    }
    
    insights.push("Priority scheduling can improve service ordering for important traffic while introducing trade-offs (like starvation) for other flows.");
    
    return insights;
  }, [simulationResults]);

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];
  const PRIORITY_COLORS = {
    'Critical': '#ef4444', 
    'High': '#f97316',     
    'Medium': '#eab308',   
    'Low': '#3b82f6'       
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8 font-sans text-gray-800">
      
      {/* HEADER & DISCLAIMER */}
      <header className="mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-gray-800 flex items-center gap-3">
                <Network className="text-blue-600 h-8 w-8" />
                AI Network Traffic Classification
              </h1>
              <p className="text-gray-500 mt-2 font-medium">
                Academic Simulation Dashboard
              </p>
            </div>
            <div className="flex flex-col items-start md:items-end gap-2">
              <div className="flex items-center gap-2">
                {backendStatus === 'Connected' ? (
                  <ShieldCheck className="text-green-500 h-5 w-5" />
                ) : backendStatus === 'Checking...' ? (
                  <Activity className="text-yellow-500 h-5 w-5" />
                ) : (
                  <ServerCrash className="text-red-500 h-5 w-5" />
                )}
                <span className={`font-medium ${
                  backendStatus === 'Connected' ? 'text-green-600' :
                  backendStatus === 'Checking...' ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  Backend API: {backendStatus}
                </span>
              </div>
            </div>
          </div>
          
          <div className="mt-6 bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r flex gap-3">
            <AlertCircle className="text-amber-500 h-6 w-6 shrink-0" />
            <div>
              <h3 className="font-bold text-amber-800">Academic Simulation Only</h3>
              <p className="text-sm text-amber-700 mt-1">
                This prototype uses synthetic traffic and simulated packet scheduling. It does not capture, transmit, or modify real network packets. Performance results are simulation outputs and should not be interpreted as real-world network benchmarks.
              </p>
            </div>
          </div>
        </div>
      </header>

      {error && (
        <div className="mb-8 flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 px-4 py-3 rounded-md shadow-sm">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span className="font-medium">{error}</span>
        </div>
      )}

      {/* SECTION 1: SYNTHETIC TRAFFIC GENERATION */}
      <section className="mb-8">
        <h2 className="text-xl font-bold text-gray-700 mb-4 flex items-center gap-2">
          <span className="bg-blue-600 text-white w-8 h-8 flex items-center justify-center rounded-full text-sm">1</span>
          Synthetic Traffic Generation
        </h2>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex flex-col md:flex-row gap-6 mb-6">
            <div className="flex-1 border-r pr-6 border-gray-100">
              <p className="text-sm text-gray-600 mb-4">Generate synthetic network flows with realistic deterministic parameters to serve as the simulation workload.</p>
              <div className="flex items-end gap-4">
                <div className="flex flex-col">
                  <label className="text-sm font-semibold text-gray-700 mb-1">Number of Flows</label>
                  <input
                    type="number"
                    min="1"
                    max="1000"
                    value={flowCount}
                    onChange={(e) => setFlowCount(e.target.value)}
                    className="border rounded-md px-3 py-2 w-32 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <button
                  onClick={handleGenerate}
                  disabled={loading || classifying || simulating}
                  className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-md transition disabled:bg-blue-300"
                >
                  {loading ? <Activity className="animate-spin h-5 w-5" /> : <Play className="h-5 w-5" />}
                  Generate Traffic
                </button>
              </div>
            </div>
            
            {stats ? (
              <div className="flex-2 flex gap-4 md:gap-8 flex-wrap items-center">
                <div className="text-center">
                  <h3 className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Total Flows</h3>
                  <p className="text-2xl font-bold text-gray-800">{flows.length}</p>
                </div>
                <div className="text-center">
                  <h3 className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Total Packets</h3>
                  <p className="text-2xl font-bold text-gray-800">{stats.totalPackets}</p>
                </div>
                <div className="text-center">
                  <h3 className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">Avg Size (B)</h3>
                  <p className="text-2xl font-bold text-gray-800">{stats.avgSize}</p>
                </div>
                <div className="h-24 w-24">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={protocolDistribution} cx="50%" cy="50%" outerRadius={30} dataKey="value">
                        {protocolDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <RechartsTooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ) : (
              <div className="flex-2 flex items-center justify-center text-gray-400 text-sm">
                No traffic generated yet.
              </div>
            )}
          </div>
        </div>
      </section>

      {/* SECTION 2: AI TRAFFIC CLASSIFICATION */}
      <section className="mb-8 opacity-100 transition-opacity">
        <h2 className="text-xl font-bold text-gray-700 mb-4 flex items-center gap-2">
          <span className="bg-indigo-600 text-white w-8 h-8 flex items-center justify-center rounded-full text-sm">2</span>
          AI Traffic Classification
        </h2>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between border-b pb-4 mb-4">
            <p className="text-sm text-gray-600 max-w-2xl">
              Evaluate the generated synthetic workload using a Random Forest machine learning pipeline. The model predicts the traffic class type (e.g. Gaming, Web Browsing) based on synthetic flow characteristics.
            </p>
            <button
              onClick={handleClassify}
              disabled={!flows.length || classifying || simulating}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-6 rounded-md transition disabled:bg-indigo-300"
            >
              {classifying ? <Activity className="animate-spin h-5 w-5" /> : <Brain className="h-5 w-5" />}
              Classify Workload
            </button>
          </div>
          
          {predictions ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2">
                <h3 className="text-sm font-bold text-gray-600 uppercase mb-3">Classification Results (First 15 flows)</h3>
                <div className="overflow-x-auto rounded border">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="p-2 border-b">Flow ID</th>
                        <th className="p-2 border-b">Proto</th>
                        <th className="p-2 border-b">Synthetic Type</th>
                        <th className="p-2 border-b text-indigo-700">Predicted Class</th>
                        <th className="p-2 border-b text-indigo-700">Confidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {flows.slice(0, 15).map((f, i) => {
                        const p = predictions[f.flowId];
                        return (
                          <tr key={i} className="border-b hover:bg-gray-50">
                            <td className="p-2 font-mono text-gray-500">{f.flowId.substring(0,6)}</td>
                            <td className="p-2">{f.protocol}</td>
                            <td className="p-2 text-gray-500">{f.groundTruthClass}</td>
                            <td className="p-2 font-semibold text-gray-800">{p.predictedClass}</td>
                            <td className="p-2">{(p.confidence * 100).toFixed(0)}%</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-bold text-gray-600 uppercase mb-3">Model Accuracy</h3>
                {mlMetrics && (
                   <div className="grid grid-cols-2 gap-3 mb-6">
                     <div className="bg-indigo-50 p-3 rounded border border-indigo-100">
                       <div className="text-xs text-indigo-800 font-bold">Accuracy</div>
                       <div className="text-xl font-bold text-indigo-900">{(mlMetrics.accuracy * 100).toFixed(1)}%</div>
                     </div>
                     <div className="bg-indigo-50 p-3 rounded border border-indigo-100">
                       <div className="text-xs text-indigo-800 font-bold">F1 Score</div>
                       <div className="text-xl font-bold text-indigo-900">{(mlMetrics.f1 * 100).toFixed(1)}%</div>
                     </div>
                   </div>
                )}
                <div className="bg-gray-50 p-4 rounded text-sm text-gray-600 border">
                  <Info className="h-5 w-5 text-blue-500 mb-2" />
                  <p>It is visually obvious here that the AI classifies traffic types based on feature matrices. It does <b>not</b> natively determine priority scheduling logic.</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-10 text-gray-400 bg-gray-50 rounded border border-dashed border-gray-200">
              <Brain className="h-10 w-10 mx-auto text-gray-300 mb-2" />
              <p>Classification results will appear here</p>
            </div>
          )}
        </div>
      </section>

      {/* SECTION 3: PRIORITY DISTRIBUTION */}
      <section className="mb-8">
        <h2 className="text-xl font-bold text-gray-700 mb-4 flex items-center gap-2">
          <span className="bg-purple-600 text-white w-8 h-8 flex items-center justify-center rounded-full text-sm">3</span>
          Priority Distribution
        </h2>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
            <div>
              <p className="text-sm text-gray-600 mb-4">
                Priority is assigned deterministically from the classified traffic class via strict application rules.
              </p>
              <div className="bg-gray-50 rounded border p-4 text-sm font-mono text-gray-700">
                <div className="flex justify-between border-b pb-2 mb-2">
                  <span>Gaming</span><span className="text-red-600 font-bold flex items-center gap-2"><ArrowRight className="h-4 w-4"/> Critical</span>
                </div>
                <div className="flex justify-between border-b pb-2 mb-2">
                  <span>VoIP</span><span className="text-red-600 font-bold flex items-center gap-2"><ArrowRight className="h-4 w-4"/> Critical</span>
                </div>
                <div className="flex justify-between border-b pb-2 mb-2">
                  <span>Video Streaming</span><span className="text-orange-500 font-bold flex items-center gap-2"><ArrowRight className="h-4 w-4"/> High</span>
                </div>
                <div className="flex justify-between border-b pb-2 mb-2">
                  <span>Web Browsing</span><span className="text-yellow-600 font-bold flex items-center gap-2"><ArrowRight className="h-4 w-4"/> Medium</span>
                </div>
                <div className="flex justify-between">
                  <span>File Transfer</span><span className="text-blue-500 font-bold flex items-center gap-2"><ArrowRight className="h-4 w-4"/> Low</span>
                </div>
              </div>
            </div>
            <div className="h-56">
              {predictions ? (
                 <ResponsiveContainer width="100%" height="100%">
                   <BarChart data={priorityDistribution} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                     <CartesianGrid strokeDasharray="3 3" />
                     <XAxis dataKey="name" />
                     <YAxis />
                     <RechartsTooltip />
                     <Bar dataKey="value" name="Assigned Flows">
                       {priorityDistribution.map((entry, index) => (
                         <Cell key={`cell-${index}`} fill={PRIORITY_COLORS[entry.name]} />
                       ))}
                     </Bar>
                   </BarChart>
                 </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-gray-400 bg-gray-50 border border-dashed rounded">
                  Classify traffic first
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4: SCHEDULING SIMULATION */}
      <section className="mb-8">
        <h2 className="text-xl font-bold text-gray-700 mb-4 flex items-center gap-2">
          <span className="bg-emerald-600 text-white w-8 h-8 flex items-center justify-center rounded-full text-sm">4</span>
          Scheduling Simulation
        </h2>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b pb-4 mb-4">
            <div className="max-w-2xl">
              <p className="text-sm text-gray-600 font-medium bg-emerald-50 text-emerald-800 p-2 rounded border border-emerald-200 mb-2">
                <span className="font-bold">Fair Comparison:</span> Both scheduling strategies are evaluated on the identical synthetic workload, sequence, processing rules, and common simulation horizon.
              </p>
            </div>
            
            <div className="flex items-center gap-4 bg-gray-50 p-2 rounded border shrink-0">
              <div className="flex flex-col">
                <label className="text-xs font-semibold text-gray-600 mb-1">Bottleneck Capacity (Pkts)</label>
                <input
                  type="number"
                  min="100"
                  value={serviceCapacity}
                  onChange={(e) => setServiceCapacity(e.target.value)}
                  className="border rounded px-2 py-1 w-32 text-sm"
                />
              </div>
              <button
                onClick={handleSimulate}
                disabled={!predictions || simulating || classifying}
                className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 px-6 rounded transition disabled:bg-emerald-300"
              >
                {simulating ? <Activity className="animate-spin h-5 w-5" /> : <Play className="h-5 w-5" />}
                Run Simulation
              </button>
            </div>
          </div>

          {simulationResults ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* FIFO Info */}
              <div className="border rounded-md overflow-hidden bg-white shadow-sm">
                <div className="bg-gray-100 border-b p-4">
                  <h3 className="font-bold text-gray-800 text-lg">FIFO Scheduling</h3>
                  <p className="text-xs text-gray-600 mt-1 font-medium">Processes flows purely according to chronological arrival sequence.</p>
                </div>
                <div className="max-h-72 overflow-y-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50 sticky top-0 shadow-sm">
                      <tr>
                        <th className="p-2 px-4 border-b">Pos</th>
                        <th className="p-2 px-4 border-b">Flow ID</th>
                        <th className="p-2 px-4 border-b">Priority</th>
                      </tr>
                    </thead>
                    <tbody>
                      {simulationResults.fifoSchedule.results.filter(r => r.serviceOrder > 0).slice(0, 50).map((r, i) => (
                        <tr key={i} className="border-b hover:bg-gray-50">
                          <td className="p-2 px-4 font-mono text-gray-500">#{r.serviceOrder}</td>
                          <td className="p-2 px-4 font-mono text-xs">{r.flowId.substring(0,6)}</td>
                          <td className="p-2 px-4 font-bold" style={{color: PRIORITY_COLORS[r.priority]}}>{r.priority}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Priority Info */}
              <div className="border rounded-md overflow-hidden bg-white shadow-sm">
                <div className="bg-emerald-50 border-b border-emerald-100 p-4">
                  <h3 className="font-bold text-emerald-900 text-lg">AI-Priority Scheduling</h3>
                  <p className="text-xs text-emerald-700 mt-1 font-medium">Processes flows according to: Critical &gt; High &gt; Medium &gt; Low.</p>
                </div>
                <div className="max-h-72 overflow-y-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-emerald-100/50 sticky top-0 shadow-sm">
                      <tr>
                        <th className="p-2 px-4 border-b">Pos</th>
                        <th className="p-2 px-4 border-b">Flow ID</th>
                        <th className="p-2 px-4 border-b">Priority</th>
                      </tr>
                    </thead>
                    <tbody>
                      {simulationResults.prioritySchedule.results.filter(r => r.serviceOrder > 0).slice(0, 50).map((r, i) => (
                        <tr key={i} className="border-b hover:bg-emerald-50/30">
                          <td className="p-2 px-4 font-mono text-emerald-600">#{r.serviceOrder}</td>
                          <td className="p-2 px-4 font-mono text-xs">{r.flowId.substring(0,6)}</td>
                          <td className="p-2 px-4 font-bold" style={{color: PRIORITY_COLORS[r.priority]}}>{r.priority}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-10 text-gray-400 bg-gray-50 rounded border border-dashed border-gray-200">
              <LayoutDashboard className="h-10 w-10 mx-auto text-gray-300 mb-2" />
              <p>Run simulation to view scheduling order</p>
            </div>
          )}
        </div>
      </section>

      {/* SECTION 5: PERFORMANCE COMPARISON */}
      <section className="mb-8">
        <h2 className="text-xl font-bold text-gray-700 mb-4 flex items-center gap-2">
          <span className="bg-teal-600 text-white w-8 h-8 flex items-center justify-center rounded-full text-sm">5</span>
          Performance Comparison
        </h2>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          
          <p className="text-sm text-gray-600 mb-6 bg-blue-50 p-3 rounded border border-blue-100">
            <b>Note:</b> Queue latency represents simulated waiting time before service. It does not represent real-world end-to-end network latency.
          </p>

          {simulationResults ? (
            <>
              {/* Metrics Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
                {[
                  { label: "Average Queue Latency (s)", key: "averageQueueLatency" },
                  { label: "Maximum Queue Latency (s)", key: "maxQueueLatency" },
                  { label: "Throughput (Mbps)", key: "throughputMbps" },
                  { label: "Packet Loss (%)", key: "packetLossPercentage" },
                  { label: "Jitter (s)", key: "jitter" },
                ].map((metric, idx) => (
                  <div key={idx} className="border rounded-md p-4 bg-gray-50 shadow-sm hover:shadow transition-shadow">
                    <h4 className="text-[11px] font-bold text-gray-500 uppercase mb-3 line-clamp-1" title={metric.label}>{metric.label}</h4>
                    <div className="flex justify-between items-center text-sm mb-2">
                      <span className="text-gray-600 font-medium">FIFO</span>
                      <span className="font-mono font-bold text-gray-800">{simulationResults.fifo[metric.key]}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm border-t pt-2 border-gray-200">
                      <span className="text-teal-700 font-bold">AI-Priority</span>
                      <span className="font-mono font-bold text-teal-900">{simulationResults.priority[metric.key]}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 border-t pt-6">
                <div className="h-64 border rounded p-4 bg-white shadow-sm">
                  <h4 className="text-sm font-bold text-gray-700 text-center mb-4">Queue Latency Comparison</h4>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={[
                        { name: "Avg Queue Latency", FIFO: simulationResults.fifo.averageQueueLatency, "AI-Priority": simulationResults.priority.averageQueueLatency },
                        { name: "Max Queue Latency", FIFO: simulationResults.fifo.maxQueueLatency, "AI-Priority": simulationResults.priority.maxQueueLatency },
                      ]}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="name" tick={{fontSize: 12, fontWeight: 500}} />
                      <YAxis tick={{fontSize: 12}} />
                      <RechartsTooltip cursor={{fill: '#f3f4f6'}} />
                      <Legend wrapperStyle={{fontSize: '12px'}} />
                      <Bar dataKey="FIFO" fill="#9ca3af" radius={[2,2,0,0]} />
                      <Bar dataKey="AI-Priority" fill="#0d9488" radius={[2,2,0,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="h-64 border rounded p-4 bg-white shadow-sm">
                  <h4 className="text-sm font-bold text-gray-700 text-center mb-4">Throughput (Mbps) & Packet Loss (%)</h4>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={[
                        { name: "Throughput", FIFO: simulationResults.fifo.throughputMbps, "AI-Priority": simulationResults.priority.throughputMbps },
                        { name: "Packet Loss", FIFO: simulationResults.fifo.packetLossPercentage, "AI-Priority": simulationResults.priority.packetLossPercentage },
                      ]}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="name" tick={{fontSize: 12, fontWeight: 500}} />
                      <YAxis tick={{fontSize: 12}} />
                      <RechartsTooltip cursor={{fill: '#f3f4f6'}} />
                      <Legend wrapperStyle={{fontSize: '12px'}} />
                      <Bar dataKey="FIFO" fill="#9ca3af" radius={[2,2,0,0]} />
                      <Bar dataKey="AI-Priority" fill="#0d9488" radius={[2,2,0,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-10 text-gray-400 bg-gray-50 rounded border border-dashed border-gray-200">
              <BarChart3 className="h-10 w-10 mx-auto text-gray-300 mb-2" />
              <p>Run simulation to view performance comparison</p>
            </div>
          )}
        </div>
      </section>

      {/* SECTION 6: SIMULATION INSIGHTS */}
      {simulationResults && (
        <section className="mb-8">
          <h2 className="text-xl font-bold text-gray-700 mb-4 flex items-center gap-2">
            <span className="bg-sky-600 text-white w-8 h-8 flex items-center justify-center rounded-full text-sm">6</span>
            Simulation Insights
          </h2>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-sky-200 bg-sky-50/30">
            <ul className="space-y-3">
              {simulationInsights.map((insight, idx) => (
                <li key={idx} className="flex gap-3 text-sm text-gray-700 font-medium">
                  <div className="w-1.5 h-1.5 rounded-full bg-sky-500 mt-2 shrink-0"></div>
                  {insight}
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {/* SECTION 7: METHODOLOGY & LIMITATIONS */}
      <section className="mb-12 border-t pt-8">
        <h2 className="text-lg font-bold text-gray-600 mb-4">Methodology & Limitations</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-600">
          <div className="bg-gray-100/50 p-5 rounded border border-gray-200">
            <h3 className="font-bold text-gray-700 mb-2">Pipeline Methodology</h3>
            <ol className="list-decimal pl-4 space-y-2 marker:text-gray-400">
              <li><b>Synthetic Traffic:</b> Controlled programmatic generation of network flows with random bounds targeting 5 distinct traffic profiles.</li>
              <li><b>Random Forest Classification:</b> Trained on synthetic datasets to predict class types based on deterministic features.</li>
              <li><b>Deterministic Priority Mapping:</b> Hardcoded structural definitions mapping prediction strings to QoS priority flags.</li>
              <li><b>FIFO / AI-Priority Simulation:</b> Memory-bound queue array iteration processing capacities sequentially.</li>
              <li><b>Performance Metrics:</b> Measured deterministically under a common comparison horizon preventing evaluation bias.</li>
            </ol>
          </div>
          <div className="bg-gray-100/50 p-5 rounded border border-gray-200">
             <h3 className="font-bold text-gray-700 mb-2">Architectural Limitations</h3>
             <ul className="list-disc pl-4 space-y-2 marker:text-gray-400">
               <li>This platform exists entirely at the application layer without any kernel, raw socket, or Scapy dependencies.</li>
               <li>"Throughput" calculation does not scale organically against TCP slow-start or congestion window sizing.</li>
               <li>"Latency" represents pure sequential buffer wait delays without mathematical regard for real-world physical layer serialization, propagation distance, or router queuing delays.</li>
               <li>Data models omit dropped-packet retransmission cycles, strictly evaluating first-pass exhaustion mapping.</li>
             </ul>
          </div>
        </div>
      </section>

    </div>
  );
}

// Temporary fallback for BarChart3 if lucide-react version doesn't have it exposed in the import above
function BarChart3(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 3v18h18" />
      <path d="M18 17V9" />
      <path d="M13 17V5" />
      <path d="M8 17v-3" />
    </svg>
  );
}

export default App;
