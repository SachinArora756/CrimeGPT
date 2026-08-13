import { useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  FileText,
  Download,
  Loader2,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Hash,
  ArrowLeft,
  Trash2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useForensicReportStore } from '../store/forensicReportStore'

export default function ForensicReportPage() {
  const { caseId } = useParams()
  const {
    readiness,
    reports,
    loading,
    generating,
    error,
    fetchReadiness,
    fetchReports,
    generateReport,
    downloadReport,
    deleteReport,
    reset,
  } = useForensicReportStore()

  useEffect(() => {
    if (caseId) {
      reset()
      fetchReadiness(caseId)
      fetchReports(caseId)
    }
  }, [caseId])

  const handleGenerate = async () => {
    if (!caseId) return
    toast.loading('Generating forensic report... This may take a few minutes.', { id: 'report-gen' })
    try {
      await generateReport(caseId)
      toast.dismiss('report-gen')
      if (!useForensicReportStore.getState().error) {
        toast.success('Forensic investigation report generated successfully!')
      } else {
        toast.error(useForensicReportStore.getState().error || 'Generation failed')
      }
    } catch (err: any) {
      toast.dismiss('report-gen')
      toast('Report generation is already in progress. Please wait.', { icon: '⏳' })
    }
  }

  const handleDownload = (docId: number) => {
    if (caseId) downloadReport(caseId, docId)
  }

  const handleDelete = async (docId: number) => {
    if (!caseId) return
    if (!window.confirm('Are you sure you want to delete this report? This action cannot be undone.')) return
    await deleteReport(caseId, docId)
    if (!useForensicReportStore.getState().error) {
      toast.success('Report deleted successfully')
    } else {
      toast.error(useForensicReportStore.getState().error || 'Failed to delete report')
    }
  }

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z')
    return d.toLocaleString()
  }

  return (
    <div className="space-y-4 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to={`/cases/${caseId}`} className="text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
            Forensic Investigation Report
          </h1>
          <p className="text-gray-500 text-xs mt-0.5">
            PRISM — Court-admissible digital forensic report
          </p>
        </div>
      </div>

      {/* Readiness Panel */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gray-800/80 border border-indigo-500/10 rounded-lg p-4"
      >
        <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          Report Readiness
        </h2>

        {loading ? (
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            Checking case readiness...
          </div>
        ) : readiness ? (
          <div className="space-y-3">
            {/* Status badge */}
            <div>
              {readiness.ready ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 rounded-md text-xs font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Ready for Generation
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-amber-500/15 text-amber-400 border border-amber-500/25 rounded-md text-xs font-medium">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Not Ready
                </span>
              )}
            </div>

            {/* Details grid */}
            <div className="grid grid-cols-3 gap-2.5">
              <div className="bg-gray-900/50 rounded-md p-2.5">
                <div className="text-[10px] text-gray-500 uppercase tracking-wider">Status</div>
                <div className="text-white text-sm font-medium mt-0.5 capitalize">
                  {readiness.case_status.replace('_', ' ')}
                </div>
              </div>
              <div className="bg-gray-900/50 rounded-md p-2.5">
                <div className="text-[10px] text-gray-500 uppercase tracking-wider">Completeness</div>
                <div className="text-white text-sm font-medium mt-0.5">
                  {readiness.completeness_score}%
                  <div className="w-full bg-gray-700 rounded-full h-1 mt-1">
                    <div
                      className={`h-1 rounded-full transition-all ${
                        readiness.completeness_score >= 80
                          ? 'bg-emerald-500'
                          : readiness.completeness_score >= 50
                          ? 'bg-amber-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${readiness.completeness_score}%` }}
                    />
                  </div>
                </div>
              </div>
              <div className="bg-gray-900/50 rounded-md p-2.5">
                <div className="text-[10px] text-gray-500 uppercase tracking-wider">Missing</div>
                <div className="text-white text-sm font-medium mt-0.5">
                  {readiness.missing_items.length === 0
                    ? 'None'
                    : `${readiness.missing_items.length} item(s)`}
                </div>
              </div>
            </div>

            {/* Missing items */}
            {readiness.missing_items.length > 0 && (
              <div className="bg-amber-500/5 border border-amber-500/15 rounded-md p-3">
                <h4 className="text-amber-400 text-xs font-medium mb-1.5">Missing:</h4>
                <ul className="space-y-0.5">
                  {readiness.missing_items.map((item, i) => (
                    <li key={i} className="text-gray-400 text-xs flex items-center gap-1.5">
                      <XCircle className="w-3 h-3 text-amber-500 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Message */}
            <p className="text-gray-500 text-xs">{readiness.message}</p>

            {/* Generate Button */}
            <div>
              <button
                onClick={handleGenerate}
                disabled={!readiness.ready || generating}
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  readiness.ready && !generating
                    ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20'
                    : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                }`}
              >
                {generating ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <FileText className="w-3.5 h-3.5" />
                    Generate PRISM Report
                  </>
                )}
              </button>
              {generating && (
                <p className="text-gray-500 text-[10px] mt-1.5">
                  This may take 2-5 minutes as AI generates each section...
                </p>
              )}
            </div>
          </div>
        ) : error ? (
          <div className="text-red-400 text-xs">{error}</div>
        ) : null}
      </motion.div>

      {/* Generated Reports */}
      {reports.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gray-800/80 border border-indigo-500/10 rounded-lg p-4"
        >
          <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            Generated Reports ({reports.length})
          </h2>

          <div className="space-y-2">
            {reports.map((report) => (
              <div
                key={report.id}
                className="flex items-center justify-between bg-gray-900/50 border border-gray-700/40 rounded-md p-3 hover:border-indigo-500/20 transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-md bg-indigo-500/15 flex items-center justify-center">
                    <FileText className="w-4 h-4 text-indigo-400" />
                  </div>
                  <div>
                    <div className="text-white font-medium text-xs">
                      PRISM Forensic Report
                    </div>
                    <div className="flex items-center gap-2.5 text-[10px] text-gray-500 mt-0.5">
                      <span className="flex items-center gap-0.5">
                        <Clock className="w-2.5 h-2.5" />
                        {formatDate(report.generated_at)}
                      </span>
                      {report.file_hash && (
                        <span className="flex items-center gap-0.5">
                          <Hash className="w-2.5 h-2.5" />
                          {report.file_hash.substring(0, 8)}
                        </span>
                      )}
                      <span className="uppercase text-indigo-400 font-medium">
                        {report.output_format}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => handleDownload(report.id)}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-indigo-600/15 text-indigo-400 border border-indigo-500/25 rounded-md text-xs hover:bg-indigo-600/25 transition-colors"
                  >
                    <Download className="w-3 h-3" />
                    Download
                  </button>
                  <button
                    onClick={() => handleDelete(report.id)}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-red-600/15 text-red-400 border border-red-500/25 rounded-md text-xs hover:bg-red-600/25 transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Info Panel */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-gray-800/40 border border-gray-700/40 rounded-lg p-4"
      >
        <h3 className="text-xs font-semibold text-gray-400 mb-2">About PRISM Reports</h3>
        <div className="grid grid-cols-2 gap-3 text-[11px] text-gray-500">
          <div>
            <p className="font-medium text-gray-400 mb-1">Structure (5 Parts):</p>
            <ul className="space-y-0.5 text-[10px]">
              <li>I: Provenance — Mandate, Authority, Credentials</li>
              <li>II: Reconstruction — Synopsis, Evidence, Findings</li>
              <li>III: Interpretation — Conclusions, Threat, Strength</li>
              <li>IV: Substantiation — Legal, Constraints, Hypotheses</li>
              <li>V: Memorandum — Opinion, Attestation, Annexures</li>
            </ul>
          </div>
          <div>
            <p className="font-medium text-gray-400 mb-1">Requirements:</p>
            <ul className="space-y-0.5 text-[10px]">
              <li>Status: Chargesheet Filed or Closed</li>
              <li>Completeness: 80%+</li>
              <li>Evidence uploaded & analyzed</li>
              <li>FIR document generated</li>
              <li>Case diary entries recorded</li>
            </ul>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
