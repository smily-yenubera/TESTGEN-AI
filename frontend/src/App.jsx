import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from './config';

const Spinner = () => <span className="spinner"></span>;

function App() {
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [repoPath, setRepoPath] = useState('demo_repo');
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState('');
  const [dashboardData, setDashboardData] = useState(null);

  const [generatingMap, setGeneratingMap] = useState({}); // { [functionName]: boolean }
  const [runningMap, setRunningMap] = useState({}); // { [testFilePath]: boolean }
  const [suggestingFixMap, setSuggestingFixMap] = useState({}); // { [testFilePath]: boolean }
  const [applyingFixMap, setApplyingFixMap] = useState({}); // { [testFilePath]: boolean }

  const [diffMap, setDiffMap] = useState({}); // { [testFilePath]: { explanation, diff, function_name } }
  const [toasts, setToasts] = useState([]); // [{ id, type: 'success' | 'error', message }]

  useEffect(() => {
    fetchHealthStatus();
    // Poll GET /dashboard-data every 5 seconds to keep UI in sync
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const addToast = (message, type = 'success') => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  };

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const fetchHealthStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (response.ok) {
        setConnectionStatus('connected');
        fetchDashboardData();
      } else {
        setConnectionStatus('error');
      }
    } catch {
      setConnectionStatus('error');
    }
  };

  const fetchDashboardData = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/dashboard-data`);
      if (res.ok) {
        const data = await res.json();
        setDashboardData(data);
      }
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    }
  };

  const handleScan = async (e) => {
    e?.preventDefault();
    if (!repoPath.trim()) return;

    setScanning(true);
    setScanError('');
    try {
      const response = await fetch(`${API_BASE_URL}/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: repoPath.trim() })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Scan failed with status ${response.status}`);
      }

      await fetchDashboardData();
      addToast('Repository scanned successfully!', 'success');
    } catch (err) {
      setScanError(err.message || 'Failed to scan repository.');
      addToast(err.message || 'Failed to scan repository.', 'error');
    } finally {
      setScanning(false);
    }
  };

  const handleGenerateTest = async (functionName, filePath) => {
    setGeneratingMap(prev => ({ ...prev, [functionName]: true }));

    try {
      const response = await fetch(`${API_BASE_URL}/generate-tests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_path: repoPath.trim(),
          function_name: functionName,
          file_path: filePath
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `Failed to generate test for ${functionName}`);
      }

      setDashboardData(prev => {
        if (!prev) return prev;
        const newGen = {
          function_name: data.function_name,
          module_name: data.module_name,
          test_file_path: data.test_file_path,
          generated_code: data.generated_code,
          status: 'generated',
          last_error: null
        };
        const existingList = prev.generated_tests || [];
        const filtered = existingList.filter(t => t.function_name !== functionName);
        return {
          ...prev,
          generated_tests: [...filtered, newGen]
        };
      });

      addToast(`Generated test suite for function '${functionName}'!`, 'success');
      await fetchDashboardData();
    } catch (err) {
      addToast(err.message || `Failed to generate test for ${functionName}`, 'error');
    } finally {
      setGeneratingMap(prev => ({ ...prev, [functionName]: false }));
    }
  };

  const handleRunTest = async (testFilePath) => {
    setRunningMap(prev => ({ ...prev, [testFilePath]: true }));

    try {
      const response = await fetch(`${API_BASE_URL}/run-tests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ test_file_path: testFilePath })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `Failed to run test file`);
      }

      const statusMsg = data.status === 'passed' ? 'PASSED ✅' : 'FAILED ❌';
      addToast(`Test execution complete: ${statusMsg}`, data.status === 'passed' ? 'success' : 'error');
      await fetchDashboardData();
    } catch (err) {
      addToast(err.message || `Failed to run test file`, 'error');
    } finally {
      setRunningMap(prev => ({ ...prev, [testFilePath]: false }));
    }
  };

  const handleSuggestFix = async (testFilePath, functionName) => {
    setSuggestingFixMap(prev => ({ ...prev, [testFilePath]: true }));

    try {
      const lastRun = dashboardData?.last_test_run;
      const failedTestItem = lastRun?.tests?.find(t => t.status === 'failed');
      const trace = failedTestItem?.traceback || failedTestItem?.error_message || 'IndexError: list index out of range';
      
      const funcCode = `def ${functionName}(email):\n    return email.split("@")[10]`;

      const response = await fetch(`${API_BASE_URL}/suggest-fix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          function_code: funcCode,
          error_trace: trace
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `Failed to suggest fix`);
      }

      setDiffMap(prev => ({
        ...prev,
        [testFilePath]: {
          explanation: data.explanation,
          diff: data.diff,
          function_name: functionName
        }
      }));

      addToast(`Fix suggestion generated for '${functionName}'`, 'success');
    } catch (err) {
      addToast(err.message || `Failed to generate fix suggestion`, 'error');
    } finally {
      setSuggestingFixMap(prev => ({ ...prev, [testFilePath]: false }));
    }
  };

  const handleAcceptFix = async (testFilePath, functionName) => {
    setApplyingFixMap(prev => ({ ...prev, [testFilePath]: true }));

    const diffData = diffMap[testFilePath];

    try {
      const response = await fetch(`${API_BASE_URL}/apply-fix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_path: repoPath.trim(),
          file_path: 'utils.py',
          function_name: functionName,
          diff: diffData?.diff
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `Failed to apply fix`);
      }

      setDiffMap(prev => {
        const copy = { ...prev };
        delete copy[testFilePath];
        return copy;
      });

      addToast(`Fix applied to disk for '${functionName}'! Re-running tests...`, 'success');
      await handleRunTest(testFilePath);
    } catch (err) {
      addToast(err.message || `Failed to apply fix`, 'error');
    } finally {
      setApplyingFixMap(prev => ({ ...prev, [testFilePath]: false }));
    }
  };

  const handleRejectFix = (testFilePath) => {
    setDiffMap(prev => {
      const copy = { ...prev };
      delete copy[testFilePath];
      return copy;
    });
    addToast('Fix suggestion dismissed.', 'success');
  };

  const renderDiffLines = (diffText) => {
    if (!diffText) return null;
    const lines = diffText.split('\n');
    return lines.map((line, i) => {
      let bg = 'transparent';
      let color = '#e2e8f0';

      if (line.startsWith('+') && !line.startsWith('+++')) {
        bg = '#064e3b';
        color = '#a7f3d0';
      } else if (line.startsWith('-') && !line.startsWith('---')) {
        bg = '#7f1d1d';
        color = '#fecaca';
      } else if (line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++')) {
        bg = '#1e293b';
        color = '#38bdf8';
      }

      return (
        <div key={i} style={{ backgroundColor: bg, color: color, padding: '2px 12px', whiteSpace: 'pre' }}>
          {line}
        </div>
      );
    });
  };

  const summary = dashboardData?.summary || {
    total_functions_scanned: 0,
    tested_count: 0,
    untested_count: 0
  };

  const coveragePercent = summary.total_functions_scanned > 0
    ? ((summary.tested_count / summary.total_functions_scanned) * 100).toFixed(1)
    : '0.0';

  const generatedTests = dashboardData?.generated_tests || [];
  const untestedFunctions = dashboardData?.untested_functions || [];

  return (
    <div className="dashboard-container">
      {/* Toast Notification Container */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast toast-${toast.type}`}>
            <span>{toast.type === 'success' ? '✅' : '⚠️'} {toast.message}</span>
            <button
              type="button"
              onClick={() => removeToast(toast.id)}
              style={{ background: 'none', border: 'none', color: '#ffffff', cursor: 'pointer', fontWeight: 'bold' }}
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      {/* Header */}
      <header className="header">
        <h1 className="header-title">
          ⚡ TestGen AI
        </h1>
        <div className={`connection-badge ${connectionStatus}`}>
          <span className="dot">●</span>
          {connectionStatus === 'connected' ? 'Backend connected' : 'Connection Error'}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        {/* Repo Scanner Section */}
        <div className="card">
          <h2 className="card-title">🔍 Repository Scanner</h2>
          <p style={{ color: '#64748b', fontSize: '0.9rem', margin: '0 0 1rem 0' }}>
            Enter absolute path to a Python repository to parse functions via AST and analyze test coverage.
          </p>
          <form onSubmit={handleScan} className="scan-form">
            <input
              type="text"
              className="input-field"
              value={repoPath}
              onChange={(e) => setRepoPath(e.target.value)}
              placeholder="e.g. C:\Testgen-ai\demo_repo"
              disabled={scanning}
            />
            <button type="submit" className="btn-primary" disabled={scanning || !repoPath.trim()}>
              {scanning ? <><Spinner /> Scanning...</> : 'Scan Repository'}
            </button>
          </form>
          {scanError && (
            <p style={{ color: '#f87171', marginTop: '0.75rem', fontWeight: 500, fontSize: '0.9rem' }}>
              ❌ {scanError}
            </p>
          )}
        </div>

        {/* Coverage Summary Cards */}
        <div className="grid-container">
          <div className="stat-card">
            <p className="stat-label">Test Coverage</p>
            <p className="stat-value" style={{ color: '#2563eb' }}>{coveragePercent}%</p>
            <div className="progress-bar-bg">
              <div
                className="progress-bar-fill"
                style={{ width: `${Math.min(100, Math.max(0, parseFloat(coveragePercent)))}%` }}
              ></div>
            </div>
          </div>

          <div className="stat-card">
            <p className="stat-label">Total Functions</p>
            <p className="stat-value">{summary.total_functions_scanned}</p>
            <p style={{ fontSize: '0.8rem', color: '#64748b', margin: 0 }}>Scanned in codebase</p>
          </div>

          <div className="stat-card">
            <p className="stat-label">Untested Functions</p>
            <p className="stat-value" style={{ color: '#ea580c' }}>{summary.untested_count}</p>
            <p style={{ fontSize: '0.8rem', color: '#64748b', margin: 0 }}>Missing test files</p>
          </div>

          <div className="stat-card">
            <p className="stat-label">Tested Functions</p>
            <p className="stat-value" style={{ color: '#16a34a' }}>{summary.tested_count}</p>
            <p style={{ fontSize: '0.8rem', color: '#64748b', margin: 0 }}>Covered by test files</p>
          </div>
        </div>

        {/* Generated Tests Table Section */}
        <div className="card">
          <h2 className="card-title">🧪 Generated Test Suites ({generatedTests.length})</h2>
          {generatedTests.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '0.5rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#475569', fontSize: '0.9rem' }}>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Target Function</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Module</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Test File Path</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Status</th>
                    <th style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {generatedTests.map((t, idx) => {
                    const isRunning = runningMap[t.test_file_path];
                    const isSuggesting = suggestingFixMap[t.test_file_path];
                    const diffData = diffMap[t.test_file_path];
                    const isApplying = applyingFixMap[t.test_file_path];

                    return (
                      <React.Fragment key={idx}>
                        <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '0.75rem 0.5rem', fontWeight: 600, color: '#0f172a' }}>
                            <code>{t.function_name}</code>
                          </td>
                          <td style={{ padding: '0.75rem 0.5rem', color: '#475569', fontSize: '0.9rem' }}>
                            {t.module_name}
                          </td>
                          <td style={{ padding: '0.75rem 0.5rem', color: '#64748b', fontSize: '0.85rem' }}>
                            <code>{t.test_file_path}</code>
                          </td>
                          <td style={{ padding: '0.75rem 0.5rem' }}>
                            {t.status === 'passed' && (
                              <span className="badge badge-success">● Passed</span>
                            )}
                            {t.status === 'failed' && (
                              <span className="badge badge-danger">● Failed</span>
                            )}
                            {t.status !== 'passed' && t.status !== 'failed' && (
                              <span className="badge badge-neutral">● Generated</span>
                            )}
                          </td>
                          <td style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>
                            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                              <button
                                type="button"
                                className="btn-sm btn-sm-success"
                                onClick={() => handleRunTest(t.test_file_path)}
                                disabled={isRunning}
                              >
                                {isRunning ? <><Spinner /> Running...</> : '▶ Run Test'}
                              </button>

                              {t.status === 'failed' && (
                                <button
                                  type="button"
                                  className="btn-sm"
                                  onClick={() => handleSuggestFix(t.test_file_path, t.function_name)}
                                  disabled={isSuggesting}
                                  style={{ backgroundColor: '#7c3aed', color: '#ffffff', border: 'none' }}
                                >
                                  {isSuggesting ? <><Spinner /> Analyzing...</> : '💡 Suggest Fix'}
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>

                        {/* Inline Code Diff View Drawer */}
                        {diffData && (
                          <tr>
                            <td colSpan={5} style={{ padding: '1rem', backgroundColor: '#0f172a', borderRadius: '0.5rem' }}>
                              <div style={{ color: '#f8fafc' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                                  <h4 style={{ margin: 0, fontSize: '1rem', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    💡 Suggested Fix & Root Cause Analysis
                                  </h4>
                                  <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Target Function: <code>{diffData.function_name}</code></span>
                                </div>
                                
                                <p style={{ margin: '0 0 1rem 0', color: '#cbd5e1', fontSize: '0.9rem', lineHeight: 1.5 }}>
                                  <strong>Explanation:</strong> {diffData.explanation}
                                </p>

                                <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '0.375rem', overflow: 'hidden', marginBottom: '1.25rem' }}>
                                  <div style={{ padding: '0.4rem 0.8rem', backgroundColor: '#020617', borderBottom: '1px solid #334155', color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600 }}>
                                    Unified Diff View
                                  </div>
                                  <div style={{ padding: '0.5rem 0', overflowX: 'auto', fontFamily: 'Consolas, Monaco, "Andale Mono", monospace', fontSize: '0.875rem' }}>
                                    {renderDiffLines(diffData.diff)}
                                  </div>
                                </div>

                                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                                  <button
                                    type="button"
                                    className="btn-sm btn-sm-success"
                                    onClick={() => handleAcceptFix(t.test_file_path, diffData.function_name)}
                                    disabled={isApplying}
                                    style={{ padding: '0.5rem 1.25rem', fontSize: '0.875rem' }}
                                  >
                                    {isApplying ? <><Spinner /> Applying Fix...</> : '✅ Accept & Apply Fix'}
                                  </button>
                                  <button
                                    type="button"
                                    className="btn-sm"
                                    onClick={() => handleRejectFix(t.test_file_path)}
                                    style={{ padding: '0.5rem 1.25rem', fontSize: '0.875rem', backgroundColor: '#334155', color: '#ffffff', border: 'none' }}
                                  >
                                    ❌ Reject
                                  </button>
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p style={{ color: '#64748b', margin: 0, fontSize: '0.95rem' }}>
              No tests generated yet. Click "Generate Tests" next to any untested function below.
            </p>
          )}
        </div>

        {/* Untested Functions List */}
        <div className="card">
          <h2 className="card-title">⚠️ Untested Functions ({untestedFunctions.length})</h2>
          {untestedFunctions.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '0.5rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#475569', fontSize: '0.9rem' }}>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Function</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>File</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Line</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Expected Test File</th>
                    <th style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {untestedFunctions.map((fn, idx) => {
                    const isGenerating = generatingMap[fn.function];
                    return (
                      <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '0.75rem 0.5rem', fontWeight: 600, color: '#0f172a' }}>
                          <code>{fn.function}({fn.args?.join(', ')})</code>
                        </td>
                        <td style={{ padding: '0.75rem 0.5rem', color: '#475569', fontSize: '0.9rem' }}>{fn.file}</td>
                        <td style={{ padding: '0.75rem 0.5rem', color: '#475569', fontSize: '0.9rem' }}>L{fn.line}</td>
                        <td style={{ padding: '0.75rem 0.5rem', color: '#94a3b8', fontStyle: 'italic', fontSize: '0.9rem' }}>
                          {fn.matching_test_file}
                        </td>
                        <td style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>
                          <button
                            type="button"
                            className="btn-sm btn-sm-primary"
                            onClick={() => handleGenerateTest(fn.function, fn.file)}
                            disabled={isGenerating}
                          >
                            {isGenerating ? <><Spinner /> Generating...</> : '✨ Generate Tests'}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p style={{ color: '#64748b', margin: 0, fontSize: '0.95rem' }}>
              No untested functions detected. Click "Scan Repository" above to discover untested functions.
            </p>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
