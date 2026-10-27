import React, { useState } from 'react';
import { Check, X, RotateCcw, ShieldCheck, AlertCircle } from 'lucide-react';
import { Button } from '../common/Button';
import { Modal } from '../common/Modal';

interface ApprovalPanelProps {
  taskId: string;
  status: string;
  onApprove: () => Promise<void>;
  onReject: () => Promise<void>;
  onRevise: (feedback: string) => Promise<void>;
  isLoading: boolean;
}

export const ApprovalPanel: React.FC<ApprovalPanelProps> = ({
  taskId,
  status,
  onApprove,
  onReject,
  onRevise,
  isLoading,
}) => {
  const [isReviseModalOpen, setIsReviseModalOpen] = useState(false);
  const [revisionNotes, setRevisionNotes] = useState('');

  const isWaitingApproval = status === 'waiting_approval';
  const isApproved = status === 'approved';
  const isRejected = status === 'rejected';

  const handleReviseSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!revisionNotes.trim()) return;
    await onRevise(revisionNotes.trim());
    setRevisionNotes('');
    setIsReviseModalOpen(false);
  };

  return (
    <>
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-2xl flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-lg ${isApproved ? 'bg-emerald-950 text-emerald-400' : isRejected ? 'bg-rose-950 text-rose-400' : 'bg-cyan-950 text-cyan-400'}`}>
            {isApproved ? (
              <Check className="w-6 h-6" />
            ) : isRejected ? (
              <X className="w-6 h-6" />
            ) : (
              <ShieldCheck className="w-6 h-6" />
            )}
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100">
              {isApproved
                ? 'Changes Applied to Repository'
                : isRejected
                ? 'Changes Rejected'
                : 'Human-in-the-Loop Review Required'}
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              {isApproved
                ? 'The proposed changes have been safely merged into the working tree.'
                : isRejected
                ? 'Staging workspace discarded. No changes were committed.'
                : 'Review the proposed code diffs and validation tests below before applying.'}
            </p>
          </div>
        </div>

        {isWaitingApproval && (
          <div className="flex items-center gap-3 w-full md:w-auto">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
              onClick={() => setIsReviseModalOpen(true)}
              disabled={isLoading}
            >
              Request Revision
            </Button>
            <Button
              variant="danger"
              size="sm"
              leftIcon={<X className="w-3.5 h-3.5" />}
              onClick={onReject}
              isLoading={isLoading}
            >
              Reject
            </Button>
            <Button
              variant="success"
              size="sm"
              leftIcon={<Check className="w-3.5 h-3.5" />}
              onClick={onApprove}
              isLoading={isLoading}
            >
              Approve Changes
            </Button>
          </div>
        )}
      </div>

      <Modal
        isOpen={isReviseModalOpen}
        onClose={() => setIsReviseModalOpen(false)}
        title="Request Agent Revision"
      >
        <form onSubmit={handleReviseSubmit} className="space-y-4">
          <p className="text-xs text-slate-400 leading-relaxed">
            Provide feedback or specific modifications to the AI agents. The orchestrator will re-execute the code generation and validation pipeline with your instructions.
          </p>

          <div>
            <textarea
              rows={4}
              placeholder="e.g. Use HS512 instead of HS256, and add a test for token expiration..."
              className="w-full bg-slate-950 border border-slate-750 focus:border-cyan-500 rounded-lg p-3 text-xs text-slate-100 placeholder-slate-500 transition-colors"
              value={revisionNotes}
              onChange={(e) => setRevisionNotes(e.target.value)}
              required
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
            <Button variant="outline" type="button" onClick={() => setIsReviseModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={isLoading}>
              Submit Revision
            </Button>
          </div>
        </form>
      </Modal>
    </>
  );
};
