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
    await generateReport(caseId)
    toast.dismiss('report-gen')
    if (!useForensicReportStore.getState().error) {
      toast.success('Forensic investigation report generated successfully!')
    } else {
      toast.error(useForensicReportStore.getState().error || 'Generation failed')
    }
  }

  const handleDownload = (docId: number) => {
    if (caseId) downloadReport(caseId, docId)
  }

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z')
    return d.toLocaleString()
  }

  return (
    <div className="space-y-6 p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to={`/cases/${caseId}`} className="text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-indigo-400" />
            Forensic Investigation Report
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            TRACE Digital Forensic Examination Report — Court-admissible format
          </p>
        </div>
      </div>

      {/* Readiness Panel */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gray-800 border border-gray-700 rounded-xl p-6"
      >
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          Report Readiness
        </h2>

        {loading ? (
          <div className="flex items-center gap-2 text-gray-400">
            <Loader2 className="w-4 h-4 animate-spin" />
            Checking case readiness...
          </div>
        ) : readiness ? (
          <div className="space-y-4">
            {/* Status badge */}
            <div className="flex items-center gap-3">
              {readiness.ready ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-lg text-sm font-medium">
                  <CheckCircle2 className="w-4 h-4" />
                  Ready for Report Generation
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-lg text-sm font-medium">
                  <AlertTriangle className="w-4 h-4" />
                  Not Ready
                </span>
              )}
            </div>

            {/* Details grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-900/50 rounded-lg p-3">
                <div className="text-xs text-gray-500 uppercase tracking-wider">Case Status</div>
                <div className="text-white font-medium mt-1 capitalize">
                  {readiness.case_status.replace('_', ' ')}
                </div>
              </div>
              <div className="bg-gray-900/50 rounded-lg p-3">
                <div className="text-xs text-gray-500 uppercase tracking-wider">Completeness</div>
                <div className="text-white font-medium mt-1">
                  {readiness.completeness_score}%
                  <div className="w-full bg-gray-700 rounded-full h-1.5 mt-1">
                    <div
                      className={`h-1.5 rounded-full transition-all ${
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
              <div className="bg-gray-900/50 rounded-lg p-3">
                <div className="text-xs text-gray-500 uppercase tracking-wider">Missing Items</div>
                <div className="text-white font-medium mt-1">
                  {readiness.missing_items.length === 0
                    ? 'None'
                    : `${readiness.missing_items.length} item(s)`}
                </div>
              </div>
            </div>

            {/* Missing items */}
            {readiness.missing_items.length > 0 && (
              <div className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-4">
                <h4 className="text-amber-400 text-sm font-medium mb-2">Missing Requirements:</h4>
                <ul className="space-y-1">
                  {readiness.missing_items.map((item, i) => (
                    <li key={i} className="text-gray-400 text-sm flex items-center gap-2">
                      <XCircle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Message */}
            <p className="text-gray-400 text-sm">{readiness.message}</p>

            {/* Generate Button */}
            <div className="pt-2">
              <button
                onClick={handleGenerate}
                disabled={!readiness.ready || generating}
                className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium transition-all ${
                  readiness.ready && !generating
                    ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20'
                    : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                }`}
              >
                {generating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating Report...
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4" />
                    Generate TRACE Forensic Report
                  </>
                )}
              </button>
              {generating && (
                <p className="text-gray-500 text-xs mt-2">
                  This may take 2-5 minutes as the AI generates each section...
                </p>
              )}
            </div>
          </div>
        ) : error ? (
          <div className="text-red-400 text-sm">{error}</div>
        ) : null}
      </motion.div>

      {/* Generated Reports */}
      {reports.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gray-800 border border-gray-700 rounded-xl p-6"
        >
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-400" />
            Generated Reports ({reports.length})
          </h2>

          <div className="space-y-3">
            {reports.map((report) => (
              <div
                key={report.id}
                className="flex items-center justify-between bg-gray-900/50 border border-gray-700/50 rounded-lg p-4 hover:border-indigo-500/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-indigo-400" />
                  </div>
                  <div>
                    <div className="text-white font-medium text-sm">
                      TRACE Forensic Investigation Report
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDate(report.generated_at)}
                      </span>
                      {report.file_hash && (
                        <span className="flex items-center gap-1">
                          <Hash className="w-3 h-3" />
                          {report.file_hash.substring(0, 8)}...
                        </span>
                      )}
                      <span className="uppercase text-indigo-400">
                        {report.output_format}
                      </span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handleDownload(report.id)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 rounded-lg text-sm hover:bg-indigo-600/30 transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download
                </button>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Info Panel */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6"
      >
        <h3 className="text-sm font-semibold text-gray-300 mb-3">About TRACE Reports</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-gray-500">
          <div>
            <p className="font-medium text-gray-400 mb-1">Report Sections Include:</p>
            <ul className="space-y-0.5">
              <li>Document Control & Executive Summary</li>
              <li>Evidence Integrity Ledger</li>
              <li>Methodology & Examination Environment</li>
              <li>Detailed Findings with Evidence Tiers</li>
              <li>Consolidated Timeline</li>
              <li>Risk Score Matrix & Legal Framework</li>
              <li>Expert Opinions & Statement of Truth</li>
              <li>Appendices (Evidence Register, Tool Log, Glossary)</li>
            </ul>
          </div>
          <div>
            <p className="font-medium text-gray-400 mb-1">Requirements:</p>
            <ul className="space-y-0.5">
              <li>Case status: Chargesheet Filed or Closed</li>
              <li>Case completeness: 80% or higher</li>
              <li>Evidence uploaded and analyzed</li>
              <li>FIR document generated</li>
              <li>Case diary entries recorded</li>
            </ul>
            <p className="font-medium text-gray-400 mt-3 mb-1">Format:</p>
            <p>Court-admissible TRACE framework (Terms, Record integrity, Analysis, Claims, Exhibits)</p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
