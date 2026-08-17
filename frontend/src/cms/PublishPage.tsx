import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Send, AlertTriangle, CheckCircle2, ShieldAlert, RefreshCw,
  FileCheck, ExternalLink, ArrowRight, History, RotateCcw, AlertOctagon, Info
} from 'lucide-react';
import { api, getActiveRole } from '../api/client';
import { ValidationReport } from '../types';

export const PublishPage: React.FC = () => {
  const queryClient = useQueryClient();
  const currentRole = getActiveRole();

  const [publishSuccessMessage, setPublishSuccessMessage] = useState<string | null>(null);
  const [publishErrorMessage, setPublishErrorMessage] = useState<string | null>(null);

  // Fetch Validation Report
  const {
    data: report,
    isLoading: isLoadingReport,
    isError: isReportError,
    refetch: refetchReport
  } = useQuery<ValidationReport>({
    queryKey: ['validation-report'],
    queryFn: () => api.getValidationReport(),
    refetchInterval: 10000 // auto-refresh every 10s
  });

  // Fetch Publish Runs
  const {
    data: runsData,
    isLoading: isLoadingRuns,
    refetch: refetchRuns
  } = useQuery({
    queryKey: ['publish-runs'],
    queryFn: () => api.getPublishRuns(1, 10)
  });

  // Publish Mutation
  const publishMutation = useMutation({
    mutationFn: (force: boolean) => api.publishCatalog(force),
    onSuccess: (data) => {
      setPublishSuccessMessage(`Catalogue published successfully! Version ${data.version} (${data.shows_count} shows, ${data.episodes_count} episodes).`);
      setPublishErrorMessage(null);
      queryClient.invalidateQueries({ queryKey: ['publish-runs'] });
      queryClient.invalidateQueries({ queryKey: ['validation-report'] });
      queryClient.invalidateQueries({ queryKey: ['catalog'] });
    },
    onError: (err: any) => {
      setPublishErrorMessage(err.message || 'Publish job failed.');
      setPublishSuccessMessage(null);
    }
  });

  // Rollback Mutation
  const rollbackMutation = useMutation({
    mutationFn: (runId: string) => api.rollbackPublish(runId),
    onSuccess: (data) => {
      alert(data.message || 'Rollback successful');
      queryClient.invalidateQueries({ queryKey: ['publish-runs'] });
      queryClient.invalidateQueries({ queryKey: ['catalog'] });
    }
  });

  const canPublish = report?.can_publish === true;
  const isAdmin = currentRole === 'admin';
  const blockingCount = report?.total_blocking_errors || 0;
  const warningCount = report?.total_warnings || 0;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 lg:p-10">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
              <FileCheck className="w-7 h-7 text-blue-500" />
              Validation & Publishing Dashboard
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Verify catalogue integrity, resolve blocking issues, and build atomic catalogue distributions.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => { refetchReport(); refetchRuns(); }}
              className="btn btn-secondary text-xs"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh Status
            </button>
          </div>
        </div>

        {/* Alerts */}
        {publishSuccessMessage && (
          <div className="p-4 bg-emerald-500/15 border border-emerald-500/30 rounded-2xl flex items-center justify-between text-sm text-emerald-300 animate-fade-in shadow-lg shadow-emerald-500/10">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              <span className="font-medium">{publishSuccessMessage}</span>
            </div>
            <a
              href="/catalog"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-200 px-3 py-1.5 rounded-lg border border-emerald-500/40 flex items-center gap-1 font-semibold"
            >
              View JSON <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        )}

        {publishErrorMessage && (
          <div className="p-4 bg-red-500/15 border border-red-500/30 rounded-2xl flex items-start gap-3 text-sm text-red-300 animate-fade-in shadow-lg shadow-red-500/10">
            <AlertOctagon className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-red-200">Publish Failed</p>
              <p className="mt-0.5">{publishErrorMessage}</p>
            </div>
          </div>
        )}

        {/* Publish Action Hero Banner */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 lg:p-8 shadow-2xl relative overflow-hidden">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
            <div className="space-y-2 max-w-2xl">
              <div className="flex items-center gap-2">
                <span
                  className={`badge ${
                    canPublish ? 'badge-published' : 'badge-error'
                  } text-xs py-1 px-3`}
                >
                  {canPublish ? 'Ready to Publish' : `${blockingCount} Blocking Issue${blockingCount === 1 ? '' : 's'}`}
                </span>
                {!isAdmin && (
                  <span className="badge bg-amber-500/15 text-amber-400 border border-amber-500/30 text-xs py-1 px-3 flex items-center gap-1">
                    <ShieldAlert className="w-3 h-3" /> Editor Role (Read-only Publish)
                  </span>
                )}
              </div>

              <h2 className="text-xl lg:text-2xl font-bold text-white">
                {canPublish
                  ? 'All validation checks passed! Ready to distribute.'
                  : 'Catalogue publishing is currently blocked.'}
              </h2>
              <p className="text-xs lg:text-sm text-slate-400 leading-relaxed">
                {canPublish
                  ? 'Publishing generates an immutable, atomically replaced catalogue.json for high-concurrency child viewer browsing.'
                  : 'Content editors must resolve all critical errors below before a new catalogue release can be published to viewers.'}
              </p>
            </div>

            {/* Action Button */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
              <button
                onClick={() => publishMutation.mutate(false)}
                disabled={!canPublish || !isAdmin || publishMutation.isPending}
                className={`btn text-sm font-bold px-6 py-3 rounded-xl shadow-lg transition-all flex items-center justify-center gap-2.5 ${
                  canPublish && isAdmin
                    ? 'btn-primary bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/30'
                    : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/60'
                }`}
              >
                {publishMutation.isPending ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Building & Storing...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Publish Catalogue
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Reason banner when disabled */}
          {(!canPublish || !isAdmin) && (
            <div className="mt-5 pt-4 border-t border-slate-800/80 flex items-start gap-2.5 text-xs text-slate-400">
              <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                {!isAdmin ? (
                  <span>
                    <strong>Role Restriction:</strong> You are currently using the <span className="text-amber-300 font-semibold">Editor</span> role. Switch to <span className="text-emerald-300 font-semibold">Admin</span> role in the top-right navbar to test publishing permissions.
                  </span>
                ) : (
                  <span>
                    <strong>Publishing Blocked:</strong> Resolve the {blockingCount} blocking error(s) listed below to enable publishing.
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Validation Report Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Validation Report ({blockingCount} Errors, {warningCount} Warnings)
            </h3>
            <span className="text-xs text-slate-400">
              Evaluated against reference.json rules
            </span>
          </div>

          {isLoadingReport ? (
            <div className="h-48 bg-slate-900 border border-slate-800 rounded-2xl animate-pulse" />
          ) : isReportError ? (
            <div className="p-6 bg-red-500/10 border border-red-500/30 rounded-2xl text-center text-red-300 text-xs">
              Failed to generate validation report from backend.
            </div>
          ) : report?.blocking_errors.length === 0 && report?.warnings.length === 0 ? (
            <div className="p-8 bg-slate-900/60 border border-slate-800 rounded-2xl text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
              <h4 className="text-sm font-bold text-white">No Issues Detected</h4>
              <p className="text-xs text-slate-400">Your content database is 100% compliant with Peblo TV streaming standards.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Critical Blocking Errors */}
              {report?.blocking_errors.map((err, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-red-950/30 border border-red-500/30 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 animate-fade-in shadow-md"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-xl bg-red-500/20 text-red-400 flex items-center justify-center shrink-0 mt-0.5">
                      <AlertOctagon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="badge badge-error text-[10px]">Blocking Error</span>
                        <span className="text-xs font-bold text-white">{err.show_title || 'Show'}</span>
                        <span className="text-[11px] text-slate-400 font-mono">({err.entity_type} {err.entity_id})</span>
                      </div>
                      <p className="text-xs text-red-200 mt-1 font-medium">{err.message}</p>
                      <p className="text-[11px] text-slate-400 mt-1">
                        <strong>Remediation:</strong> {err.remediation}
                      </p>
                    </div>
                  </div>

                  <a
                    href="/cms"
                    className="btn btn-secondary text-xs shrink-0 self-start md:self-center border-red-500/40 hover:bg-red-500/10 text-red-200"
                  >
                    Fix in CMS <ArrowRight className="w-3.5 h-3.5" />
                  </a>
                </div>
              ))}

              {/* Non-blocking Warnings */}
              {report?.warnings.map((warn, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-amber-950/20 border border-amber-500/30 rounded-2xl flex items-start gap-3 animate-fade-in"
                >
                  <div className="w-8 h-8 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="badge badge-draft text-[10px]">Warning</span>
                      <span className="text-xs font-bold text-white">{warn.show_title || 'Show'}</span>
                    </div>
                    <p className="text-xs text-amber-200 mt-1 font-medium">{warn.message}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      <strong>Remediation:</strong> {warn.remediation}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Publish Run History */}
        <div className="space-y-4 pt-6 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <History className="w-5 h-5 text-blue-400" />
              Publish Run History
            </h3>
            <span className="text-xs text-slate-400">Past immutable catalogue builds</span>
          </div>

          {isLoadingRuns ? (
            <div className="h-36 bg-slate-900 border border-slate-800 rounded-2xl animate-pulse" />
          ) : (runsData?.items || []).length === 0 ? (
            <div className="p-8 text-center bg-slate-900/40 border border-slate-800 rounded-2xl text-xs text-slate-400">
              No previous publish runs recorded yet.
            </div>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Version & Timestamp</th>
                    <th className="py-3 px-4">Initiated By</th>
                    <th className="py-3 px-4">Shows / Episodes</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {runsData?.items.map((run) => {
                    const dateStr = new Date(run.started_at).toLocaleString();
                    return (
                      <tr key={run.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4">
                          <span className="font-mono font-bold text-white block">
                            {run.catalogue_version || 'v1'}
                          </span>
                          <span className="text-[11px] text-slate-400">{dateStr}</span>
                        </td>
                        <td className="py-3 px-4 text-slate-300">{run.initiated_by}</td>
                        <td className="py-3 px-4 text-slate-300">
                          <strong>{run.shows_count}</strong> shows / <strong>{run.episodes_count}</strong> eps
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`badge ${
                              run.status === 'success' ? 'badge-published' : 'badge-error'
                            }`}
                          >
                            {run.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          {run.status === 'success' && isAdmin && (
                            <button
                              onClick={() => {
                                if (confirm(`Rollback live catalogue to version ${run.catalogue_version}?`)) {
                                  rollbackMutation.mutate(run.id);
                                }
                              }}
                              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 ml-auto"
                              title="Rollback to this snapshot"
                            >
                              <RotateCcw className="w-3.5 h-3.5" /> Rollback
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
