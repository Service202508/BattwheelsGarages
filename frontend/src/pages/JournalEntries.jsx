import React, { useState, useEffect, useCallback } from 'react';
import { 
  ChevronDown, ChevronRight, Plus, Download, Search, 
  Check, X, Calendar, FileText, Filter
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Design tokens — using CSS variables
const colors = {
  pageBg: 'rgb(var(--bw-off-black))',
  cardBg: 'rgb(var(--bw-panel))',
  cardHover: 'rgb(var(--bw-card))',
  border: 'var(--bw-border)',
  volt: 'rgb(var(--bw-volt))',
  voltDim: 'rgb(var(--bw-volt) / 0.15)',
  white: 'rgb(var(--bw-white))',
  muted: 'var(--bw-muted)',
  green: 'rgb(var(--bw-green))',
  greenBg: 'rgb(var(--bw-green) / 0.10)',
  greenBorder: 'rgb(var(--bw-green) / 0.25)',
  red: 'rgb(var(--bw-red))',
  redBg: 'rgb(var(--bw-red) / 0.10)',
  redBorder: 'rgb(var(--bw-red) / 0.25)',
  blue: 'rgb(var(--bw-blue))',
  blueBg: 'rgb(var(--bw-blue) / 0.15)',
  orange: 'rgb(var(--bw-orange))',
  orangeBg: 'rgb(var(--bw-orange) / 0.15)',
  amber: 'rgb(var(--bw-amber))',
  amberBg: 'rgb(var(--bw-amber) / 0.15)',
  cyan: 'rgb(var(--bw-teal))',
  cyanBg: 'rgb(var(--bw-teal) / 0.15)',
};

// Entry type color mapping
const entryTypeColors = {
  SALES: { bg: colors.voltDim, text: colors.volt, border: 'rgba(200,255,0,0.3)' },
  PURCHASE: { bg: colors.blueBg, text: colors.blue, border: 'rgba(59,130,246,0.3)' },
  PAYMENT: { bg: colors.greenBg, text: colors.green, border: colors.greenBorder },
  RECEIPT: { bg: colors.greenBg, text: colors.green, border: colors.greenBorder },
  EXPENSE: { bg: colors.orangeBg, text: colors.orange, border: 'rgba(249,115,22,0.3)' },
  PAYROLL: { bg: colors.amberBg, text: colors.amber, border: 'rgba(245,158,11,0.3)' },
  DEPRECIATION: { bg: 'rgba(255,255,255,0.05)', text: colors.muted, border: colors.border },
  JOURNAL: { bg: colors.cyanBg, text: colors.cyan, border: 'rgba(6,182,212,0.3)' },
  OPENING: { bg: colors.voltDim, text: colors.volt, border: 'rgba(200,255,0,0.3)' },
  ADJUSTMENT: { bg: colors.orangeBg, text: colors.orange, border: 'rgba(249,115,22,0.3)' },
};

// Format currency
const formatCurrency = (amount) => {
  if (!amount && amount !== 0) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

// Stat Card Component
const StatCard = ({ label, value, format = 'number', status = null }) => {
  let displayValue = value;
  let valueColor = colors.volt;
  let bgColor = 'transparent';
  let borderColor = colors.border;

  if (format === 'currency') {
    displayValue = formatCurrency(value);
  } else if (format === 'status') {
    if (value === 'BALANCED' || value === true) {
      displayValue = 'BALANCED';
      valueColor = colors.green;
      bgColor = colors.greenBg;
      borderColor = colors.greenBorder;
    } else {
      displayValue = 'ERROR';
      valueColor = colors.red;
      bgColor = colors.redBg;
      borderColor = colors.redBorder;
    }
  }

  return (
    <div 
      style={{
        background: bgColor || colors.cardBg,
        border: `1px solid ${borderColor}`,
        borderRadius: '4px',
        padding: '16px 20px',
      }}
    >
      <div style={{ 
        fontFamily: 'JetBrains Mono, monospace', 
        fontSize: '10px', 
        textTransform: 'uppercase',
        color: colors.muted,
        marginBottom: '8px',
        letterSpacing: '0.5px'
      }}>
        {label}
      </div>
      <div style={{ 
        fontFamily: format === 'status' ? 'JetBrains Mono, monospace' : 'Syne, sans-serif',
        fontSize: format === 'status' ? '16px' : '20px',
        fontWeight: 700,
        color: valueColor,
        letterSpacing: format === 'status' ? '1px' : '0'
      }}>
        {displayValue}
      </div>
    </div>
  );
};

// Entry Type Pill
const EntryTypePill = ({ type }) => {
  const typeColors = entryTypeColors[type] || entryTypeColors.JOURNAL;
  return (
    <span style={{
      display: 'inline-block',
      padding: '4px 10px',
      borderRadius: '4px',
      fontSize: '11px',
      fontFamily: 'JetBrains Mono, monospace',
      fontWeight: 600,
      background: typeColors.bg,
      color: typeColors.text,
      border: `1px solid ${typeColors.border}`,
      textTransform: 'uppercase',
    }}>
      {type}
    </span>
  );
};

// Status Pill
const StatusPill = ({ status }) => {
  const isPosted = status === 'posted' || status === true;
  return (
    <span style={{
      display: 'inline-block',
      padding: '4px 8px',
      borderRadius: '4px',
      fontSize: '10px',
      fontFamily: 'JetBrains Mono, monospace',
      fontWeight: 600,
      background: isPosted ? colors.greenBg : colors.amberBg,
      color: isPosted ? colors.green : colors.amber,
      border: `1px solid ${isPosted ? colors.greenBorder : 'rgba(245,158,11,0.3)'}`,
      textTransform: 'uppercase',
    }}>
      {isPosted ? 'POSTED' : 'DRAFT'}
    </span>
  );
};

// Expanded Entry Lines Component
const EntryLines = ({ lines }) => {
  const totalDebit = lines.reduce((sum, l) => sum + (l.debit_amount || 0), 0);
  const totalCredit = lines.reduce((sum, l) => sum + (l.credit_amount || 0), 0);
  const isBalanced = Math.abs(totalDebit - totalCredit) < 0.01;

  return (
    <div style={{ 
      background: 'rgba(0,0,0,0.3)', 
      borderRadius: '4px',
      margin: '8px 0 8px 40px',
      overflow: 'hidden'
    }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: 'rgb(255 255 255 / 0.03)' }}>
            <th style={{ 
              padding: '10px 16px', 
              textAlign: 'left',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '10px',
              textTransform: 'uppercase',
              color: colors.muted,
              fontWeight: 500,
              letterSpacing: '0.5px'
            }}>Account Code</th>
            <th style={{ 
              padding: '10px 16px', 
              textAlign: 'left',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '10px',
              textTransform: 'uppercase',
              color: colors.muted,
              fontWeight: 500,
              letterSpacing: '0.5px'
            }}>Account Name</th>
            <th style={{ 
              padding: '10px 16px', 
              textAlign: 'right',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '10px',
              textTransform: 'uppercase',
              color: colors.muted,
              fontWeight: 500,
              letterSpacing: '0.5px'
            }}>Debit ₹</th>
            <th style={{ 
              padding: '10px 16px', 
              textAlign: 'right',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '10px',
              textTransform: 'uppercase',
              color: colors.muted,
              fontWeight: 500,
              letterSpacing: '0.5px'
            }}>Credit ₹</th>
          </tr>
        </thead>
        <tbody>
          {lines.map((line, idx) => (
            <tr key={line.line_id || idx} style={{ borderBottom: `1px solid ${colors.border}` }}>
              <td style={{ 
                padding: '12px 16px',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '11px',
                color: colors.volt
              }}>
                {line.account_code}
              </td>
              <td style={{ 
                padding: '12px 16px',
                fontFamily: 'Syne, sans-serif',
                fontSize: '13px',
                color: colors.white
              }}>
                {line.account_name}
                {line.description && (
                  <span style={{ color: colors.muted, marginLeft: '8px', fontSize: '12px' }}>
                    — {line.description}
                  </span>
                )}
              </td>
              <td style={{ 
                padding: '12px 16px',
                textAlign: 'right',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '13px',
                color: line.debit_amount > 0 ? colors.green : colors.muted,
                fontWeight: line.debit_amount > 0 ? 600 : 400
              }}>
                {line.debit_amount > 0 ? formatCurrency(line.debit_amount) : '—'}
              </td>
              <td style={{ 
                padding: '12px 16px',
                textAlign: 'right',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '13px',
                color: line.credit_amount > 0 ? colors.blue : colors.muted,
                fontWeight: line.credit_amount > 0 ? 600 : 400
              }}>
                {line.credit_amount > 0 ? formatCurrency(line.credit_amount) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr style={{ 
            background: 'rgb(var(--bw-volt) / 0.06)',
            borderTop: `1px solid rgba(200,255,0,0.20)`
          }}>
            <td colSpan="2" style={{ 
              padding: '12px 16px',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '11px',
              fontWeight: 700,
              color: colors.white,
              textTransform: 'uppercase'
            }}>
              TOTAL
              <span style={{ 
                marginLeft: '16px',
                color: isBalanced ? colors.green : colors.red,
                fontWeight: 700
              }}>
                {isBalanced ? '✓ BALANCED' : '✗ ERROR'}
              </span>
            </td>
            <td style={{ 
              padding: '12px 16px',
              textAlign: 'right',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '13px',
              color: colors.green,
              fontWeight: 700
            }}>
              {formatCurrency(totalDebit)}
            </td>
            <td style={{ 
              padding: '12px 16px',
              textAlign: 'right',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '13px',
              color: colors.blue,
              fontWeight: 700
            }}>
              {formatCurrency(totalCredit)}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
};

// Manual Journal Entry Modal
const JournalEntryModal = ({ isOpen, onClose, accounts, onSuccess }) => {
  const [entryDate, setEntryDate] = useState(new Date().toISOString().split('T')[0]);
  const [description, setDescription] = useState('');
  const [narration, setNarration] = useState('');
  const [lines, setLines] = useState([
    { account_id: '', description: '', debit_amount: '', credit_amount: '' },
    { account_id: '', description: '', debit_amount: '', credit_amount: '' },
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const totalDebit = lines.reduce((sum, l) => sum + (parseFloat(l.debit_amount) || 0), 0);
  const totalCredit = lines.reduce((sum, l) => sum + (parseFloat(l.credit_amount) || 0), 0);
  const difference = Math.abs(totalDebit - totalCredit);
  const isBalanced = difference < 0.01 && totalDebit > 0;

  const addLine = () => {
    setLines([...lines, { account_id: '', description: '', debit_amount: '', credit_amount: '' }]);
  };

  const updateLine = (idx, field, value) => {
    const newLines = [...lines];
    newLines[idx][field] = value;
    setLines(newLines);
  };

  const removeLine = (idx) => {
    if (lines.length > 2) {
      setLines(lines.filter((_, i) => i !== idx));
    }
  };

  const handleSubmit = async () => {
    if (!isBalanced) return;
    
    setSubmitting(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/journal-entries`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-Organization-ID': localStorage.getItem('organization_id') || ''
        },
        credentials: 'include',
        body: JSON.stringify({
          entry_date: entryDate,
          description: description,
          entry_type: 'JOURNAL',
          lines: lines.filter(l => l.account_id).map(l => ({
            account_id: l.account_id,
            description: l.description,
            debit_amount: parseFloat(l.debit_amount) || 0,
            credit_amount: parseFloat(l.credit_amount) || 0,
          }))
        })
      });

      const data = await response.json();
      
      if (data.code === 0) {
        onSuccess();
        onClose();
        // Reset form
        setDescription('');
        setNarration('');
        setLines([
          { account_id: '', description: '', debit_amount: '', credit_amount: '' },
          { account_id: '', description: '', debit_amount: '', credit_amount: '' },
        ]);
      } else {
        setError(data.detail || data.message || 'Failed to create entry');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div style={{
        background: colors.cardBg,
        border: `1px solid ${colors.border}`,
        borderRadius: '4px',
        width: '100%',
        maxWidth: '900px',
        maxHeight: '90vh',
        overflow: 'auto'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: `1px solid ${colors.border}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h2 style={{ 
              fontFamily: 'Syne, sans-serif', 
              fontSize: '18px', 
              fontWeight: 700,
              color: colors.white,
              margin: 0
            }}>
              New Journal Entry
            </h2>
            <p style={{ 
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '11px',
              color: colors.muted,
              margin: '4px 0 0 0'
            }}>
              Manual double-entry journal posting
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: colors.muted,
              cursor: 'pointer',
              padding: '8px',
              fontSize: '20px'
            }}
          >
            ×
          </button>
        </div>

        {/* Form */}
        <div style={{ padding: '24px' }}>
          {/* Top fields */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '16px', marginBottom: '24px' }}>
            <div>
              <label style={{ 
                display: 'block',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '10px',
                textTransform: 'uppercase',
                color: colors.muted,
                marginBottom: '8px'
              }}>Entry Date</label>
              <input
                type="date"
                value={entryDate}
                onChange={(e) => setEntryDate(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  background: colors.pageBg,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  color: colors.white,
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '13px'
                }}
              />
            </div>
            <div>
              <label style={{ 
                display: 'block',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '10px',
                textTransform: 'uppercase',
                color: colors.muted,
                marginBottom: '8px'
              }}>Description *</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Journal entry description"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  background: colors.pageBg,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  color: colors.white,
                  fontFamily: 'Syne, sans-serif',
                  fontSize: '13px'
                }}
              />
            </div>
          </div>

          {/* Line items */}
          <div style={{ marginBottom: '24px' }}>
            <label style={{ 
              display: 'block',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '10px',
              textTransform: 'uppercase',
              color: colors.muted,
              marginBottom: '12px'
            }}>Entry Lines</label>
            
            <div style={{ 
              background: colors.pageBg, 
              borderRadius: '4px',
              border: `1px solid ${colors.border}`,
              overflow: 'hidden'
            }}>
              {/* Table header */}
              <div style={{ 
                display: 'grid',
                gridTemplateColumns: '2fr 1.5fr 1fr 1fr 40px',
                gap: '8px',
                padding: '10px 12px',
                background: 'rgb(255 255 255 / 0.03)',
                borderBottom: `1px solid ${colors.border}`
              }}>
                <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', textTransform: 'uppercase', color: colors.muted }}>Account</span>
                <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', textTransform: 'uppercase', color: colors.muted }}>Description</span>
                <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', textTransform: 'uppercase', color: colors.muted, textAlign: 'right' }}>Debit ₹</span>
                <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', textTransform: 'uppercase', color: colors.muted, textAlign: 'right' }}>Credit ₹</span>
                <span></span>
              </div>
              
              {/* Line rows */}
              {lines.map((line, idx) => (
                <div key={idx} style={{ 
                  display: 'grid',
                  gridTemplateColumns: '2fr 1.5fr 1fr 1fr 40px',
                  gap: '8px',
                  padding: '8px 12px',
                  borderBottom: `1px solid ${colors.border}`,
                  alignItems: 'center'
                }}>
                  <select
                    value={line.account_id}
                    onChange={(e) => updateLine(idx, 'account_id', e.target.value)}
                    style={{
                      padding: '8px',
                      background: colors.cardBg,
                      border: `1px solid ${colors.border}`,
                      borderRadius: '4px',
                      color: colors.white,
                      fontSize: '12px'
                    }}
                  >
                    <option value="">Select account...</option>
                    {accounts.map(acc => (
                      <option key={acc.account_id} value={acc.account_id}>
                        {acc.account_code} - {acc.account_name}
                      </option>
                    ))}
                  </select>
                  <input
                    type="text"
                    value={line.description}
                    onChange={(e) => updateLine(idx, 'description', e.target.value)}
                    placeholder="Line description"
                    style={{
                      padding: '8px',
                      background: colors.cardBg,
                      border: `1px solid ${colors.border}`,
                      borderRadius: '4px',
                      color: colors.white,
                      fontSize: '12px'
                    }}
                  />
                  <input
                    type="number"
                    value={line.debit_amount}
                    onChange={(e) => updateLine(idx, 'debit_amount', e.target.value)}
                    placeholder="0.00"
                    style={{
                      padding: '8px',
                      background: colors.cardBg,
                      border: `1px solid ${colors.border}`,
                      borderRadius: '4px',
                      color: colors.green,
                      fontSize: '12px',
                      textAlign: 'right',
                      fontFamily: 'JetBrains Mono, monospace'
                    }}
                  />
                  <input
                    type="number"
                    value={line.credit_amount}
                    onChange={(e) => updateLine(idx, 'credit_amount', e.target.value)}
                    placeholder="0.00"
                    style={{
                      padding: '8px',
                      background: colors.cardBg,
                      border: `1px solid ${colors.border}`,
                      borderRadius: '4px',
                      color: colors.blue,
                      fontSize: '12px',
                      textAlign: 'right',
                      fontFamily: 'JetBrains Mono, monospace'
                    }}
                  />
                  <button
                    onClick={() => removeLine(idx)}
                    disabled={lines.length <= 2}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: lines.length > 2 ? colors.red : colors.muted,
                      cursor: lines.length > 2 ? 'pointer' : 'not-allowed',
                      fontSize: '16px',
                      padding: '4px'
                    }}
                  >
                    ×
                  </button>
                </div>
              ))}
              
              {/* Add line button */}
              <div style={{ padding: '12px' }}>
                <button
                  onClick={addLine}
                  style={{
                    background: 'transparent',
                    border: `1px dashed ${colors.border}`,
                    borderRadius: '4px',
                    color: colors.volt,
                    padding: '8px 16px',
                    cursor: 'pointer',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '11px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <Plus size={14} /> Add Line
                </button>
              </div>
            </div>
          </div>

          {/* Balance checker */}
          <div style={{
            background: isBalanced ? colors.greenBg : colors.redBg,
            border: `1px solid ${isBalanced ? colors.greenBorder : colors.redBorder}`,
            borderRadius: '4px',
            padding: '16px 20px',
            marginBottom: '24px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '32px' }}>
                <div>
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Total Debits</span>
                  <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '16px', color: colors.green, fontWeight: 700 }}>
                    {formatCurrency(totalDebit)}
                  </div>
                </div>
                <div>
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Total Credits</span>
                  <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '16px', color: colors.blue, fontWeight: 700 }}>
                    {formatCurrency(totalCredit)}
                  </div>
                </div>
                <div>
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: colors.muted, textTransform: 'uppercase' }}>Difference</span>
                  <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '16px', color: isBalanced ? colors.green : colors.red, fontWeight: 700 }}>
                    {formatCurrency(difference)}
                  </div>
                </div>
              </div>
              <div style={{ 
                fontFamily: 'JetBrains Mono, monospace', 
                fontSize: '12px', 
                color: isBalanced ? colors.green : colors.red,
                fontWeight: 700
              }}>
                {isBalanced ? '✓ BALANCED' : '✗ Entry must balance before posting'}
              </div>
            </div>
          </div>

          {/* Error message */}
          {error && (
            <div style={{
              background: colors.redBg,
              border: `1px solid ${colors.redBorder}`,
              borderRadius: '4px',
              padding: '12px 16px',
              marginBottom: '16px',
              color: colors.red,
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '12px'
            }}>
              {error}
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <button
              onClick={onClose}
              style={{
                padding: '10px 20px',
                background: 'transparent',
                border: `1px solid ${colors.border}`,
                borderRadius: '4px',
                color: colors.muted,
                cursor: 'pointer',
                fontFamily: 'Syne, sans-serif',
                fontSize: '13px'
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!isBalanced || !description || submitting}
              style={{
                padding: '10px 24px',
                background: isBalanced && description ? colors.volt : colors.muted,
                border: 'none',
                borderRadius: '4px',
                color: colors.pageBg,
                cursor: isBalanced && description ? 'pointer' : 'not-allowed',
                fontFamily: 'Syne, sans-serif',
                fontSize: '13px',
                fontWeight: 700,
                opacity: isBalanced && description ? 1 : 0.5
              }}
            >
              {submitting ? 'Posting...' : 'Post Journal Entry'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Account Ledger Tab
const AccountLedgerTab = ({ accounts }) => {
  const [selectedAccount, setSelectedAccount] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [ledgerData, setLedgerData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchLedger = useCallback(async () => {
    if (!selectedAccount) return;
    
    setLoading(true);
    try {
      let url = `${API_URL}/api/journal-entries/accounts/${selectedAccount}/ledger`;
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (params.toString()) url += `?${params.toString()}`;

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-Organization-ID': localStorage.getItem('organization_id') || ''
        },
        credentials: 'include'
      });
      const data = await response.json();
      if (data.code === 0) {
        setLedgerData(data);
      }
    } catch (err) {
      console.error('Error fetching ledger:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedAccount, startDate, endDate]);

  useEffect(() => {
    if (selectedAccount) {
      fetchLedger();
    }
  }, [selectedAccount, fetchLedger]);

  return (
    <div>
      {/* Filters */}
      <div style={{ 
        display: 'flex', 
        gap: '16px', 
        marginBottom: '24px',
        padding: '16px 20px',
        background: colors.cardBg,
        border: `1px solid ${colors.border}`,
        borderRadius: '4px'
      }}>
        <div style={{ flex: 2 }}>
          <label style={{ 
            display: 'block',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '10px',
            textTransform: 'uppercase',
            color: colors.muted,
            marginBottom: '8px'
          }}>Select Account</label>
          <select
            value={selectedAccount}
            onChange={(e) => setSelectedAccount(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              background: colors.pageBg,
              border: `1px solid ${colors.border}`,
              borderRadius: '4px',
              color: colors.white,
              fontSize: '13px'
            }}
          >
            <option value="">Choose an account...</option>
            {accounts.map(acc => (
              <option key={acc.account_id} value={acc.account_id}>
                {acc.account_code} - {acc.account_name} ({acc.account_type})
              </option>
            ))}
          </select>
        </div>
        <div style={{ flex: 1 }}>
          <label style={{ 
            display: 'block',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '10px',
            textTransform: 'uppercase',
            color: colors.muted,
            marginBottom: '8px'
          }}>From Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              background: colors.pageBg,
              border: `1px solid ${colors.border}`,
              borderRadius: '4px',
              color: colors.white,
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '13px'
            }}
          />
        </div>
        <div style={{ flex: 1 }}>
          <label style={{ 
            display: 'block',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '10px',
            textTransform: 'uppercase',
            color: colors.muted,
            marginBottom: '8px'
          }}>To Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              background: colors.pageBg,
              border: `1px solid ${colors.border}`,
              borderRadius: '4px',
              color: colors.white,
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '13px'
            }}
          />
        </div>
      </div>

      {/* Ledger table */}
      {!selectedAccount ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '60px 20px',
          color: colors.muted,
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: '13px'
        }}>
          Select an account to view its ledger
        </div>
      ) : loading ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '60px 20px',
          color: colors.muted
        }}>
          Loading...
        </div>
      ) : ledgerData ? (
        <div style={{ 
          background: colors.cardBg,
          border: `1px solid ${colors.border}`,
          borderRadius: '4px',
          overflow: 'hidden'
        }}>
          {/* Account header */}
          <div style={{ 
            padding: '16px 20px',
            borderBottom: `1px solid ${colors.border}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <span style={{ 
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '12px',
                color: colors.volt,
                marginRight: '12px'
              }}>
                {ledgerData.account_code}
              </span>
              <span style={{ 
                fontFamily: 'Syne, sans-serif',
                fontSize: '16px',
                color: colors.white,
                fontWeight: 600
              }}>
                {ledgerData.account_name}
              </span>
              <span style={{ 
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '11px',
                color: colors.muted,
                marginLeft: '12px',
                textTransform: 'uppercase'
              }}>
                {ledgerData.account_type}
              </span>
            </div>
          </div>

          {/* Table */}
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'rgb(255 255 255 / 0.03)' }}>
                {['Date', 'Ref No.', 'Description', 'Debit ₹', 'Credit ₹', 'Running Balance ₹'].map(h => (
                  <th key={h} style={{ 
                    padding: '12px 16px',
                    textAlign: h.includes('₹') ? 'right' : 'left',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '10px',
                    textTransform: 'uppercase',
                    color: colors.muted,
                    fontWeight: 500,
                    letterSpacing: '0.5px'
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Opening balance */}
              <tr style={{ background: 'rgb(var(--bw-volt) / 0.06)' }}>
                <td colSpan="5" style={{ 
                  padding: '12px 16px',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '11px',
                  color: colors.volt,
                  fontWeight: 600
                }}>
                  OPENING BALANCE
                </td>
                <td style={{ 
                  padding: '12px 16px',
                  textAlign: 'right',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '13px',
                  color: ledgerData.opening_balance >= 0 ? colors.green : colors.red,
                  fontWeight: 700
                }}>
                  {formatCurrency(ledgerData.opening_balance)}
                </td>
              </tr>
              
              {/* Transactions */}
              {ledgerData.entries.map((entry, idx) => (
                <tr key={idx} style={{ borderBottom: `1px solid ${colors.border}` }}>
                  <td style={{ 
                    padding: '12px 16px',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '12px',
                    color: colors.muted
                  }}>
                    {entry.entry_date}
                  </td>
                  <td style={{ 
                    padding: '12px 16px',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '12px',
                    color: colors.volt
                  }}>
                    {entry.reference_number}
                  </td>
                  <td style={{ 
                    padding: '12px 16px',
                    fontFamily: 'Syne, sans-serif',
                    fontSize: '13px',
                    color: colors.white
                  }}>
                    {entry.description}
                    {entry.line_description && (
                      <span style={{ color: colors.muted, marginLeft: '8px', fontSize: '12px' }}>
                        — {entry.line_description}
                      </span>
                    )}
                  </td>
                  <td style={{ 
                    padding: '12px 16px',
                    textAlign: 'right',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '13px',
                    color: entry.debit_amount > 0 ? colors.green : colors.muted
                  }}>
                    {entry.debit_amount > 0 ? formatCurrency(entry.debit_amount) : '—'}
                  </td>
                  <td style={{ 
                    padding: '12px 16px',
                    textAlign: 'right',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '13px',
                    color: entry.credit_amount > 0 ? colors.blue : colors.muted
                  }}>
                    {entry.credit_amount > 0 ? formatCurrency(entry.credit_amount) : '—'}
                  </td>
                  <td style={{ 
                    padding: '12px 16px',
                    textAlign: 'right',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '13px',
                    fontWeight: 600,
                    color: entry.running_balance > 0 ? colors.green : entry.running_balance < 0 ? colors.red : 'rgba(244,246,240,0.20)'
                  }}>
                    {formatCurrency(entry.running_balance)}
                  </td>
                </tr>
              ))}
              
              {/* Closing balance */}
              <tr style={{ background: 'rgb(var(--bw-volt) / 0.06)' }}>
                <td colSpan="3" style={{ 
                  padding: '12px 16px',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '11px',
                  color: colors.volt,
                  fontWeight: 600
                }}>
                  CLOSING BALANCE
                </td>
                <td style={{ 
                  padding: '12px 16px',
                  textAlign: 'right',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '13px',
                  color: colors.green,
                  fontWeight: 700
                }}>
                  {formatCurrency(ledgerData.total_debit)}
                </td>
                <td style={{ 
                  padding: '12px 16px',
                  textAlign: 'right',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '13px',
                  color: colors.blue,
                  fontWeight: 700
                }}>
                  {formatCurrency(ledgerData.total_credit)}
                </td>
                <td style={{ 
                  padding: '12px 16px',
                  textAlign: 'right',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '14px',
                  fontWeight: 700,
                  color: ledgerData.closing_balance >= 0 ? colors.green : colors.red
                }}>
                  {formatCurrency(ledgerData.closing_balance)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
};

// Main Journal Entries Page
const JournalEntries = () => {
  const [activeTab, setActiveTab] = useState('entries');
  const [entries, setEntries] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [stats, setStats] = useState({ total: 0, totalDebit: 0, totalCredit: 0, isBalanced: true });
  const [loading, setLoading] = useState(true);
  const [expandedEntry, setExpandedEntry] = useState(null);
  const [showModal, setShowModal] = useState(false);
  
  // Filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [entryType, setEntryType] = useState('');
  const [accountFilter, setAccountFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch entries
      let entriesUrl = `${API_URL}/api/journal-entries`;
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (entryType) params.append('entry_type', entryType);
      if (accountFilter) params.append('account_id', accountFilter);
      params.append('limit', '100');
      if (params.toString()) entriesUrl += `?${params.toString()}`;

      const token = localStorage.getItem('token');
      const orgId = localStorage.getItem('organization_id');
      const authHeaders = { Authorization: `Bearer ${token}`, 'X-Organization-ID': orgId || '' };

      const [entriesRes, accountsRes, trialRes] = await Promise.all([
        fetch(entriesUrl, { headers: authHeaders, credentials: 'include' }),
        fetch(`${API_URL}/api/journal-entries/accounts/chart`, { headers: authHeaders, credentials: 'include' }),
        fetch(`${API_URL}/api/journal-entries/reports/trial-balance`, { headers: authHeaders, credentials: 'include' })
      ]);

      const entriesData = await entriesRes.json();
      const accountsData = await accountsRes.json();
      const trialData = await trialRes.json();

      // API returns paginated {data: [...], pagination: {...}} format
      const rawEntries = entriesData.data || entriesData.entries || [];
      let filtered = rawEntries;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        filtered = filtered.filter(e =>
          e.reference_number?.toLowerCase().includes(q) ||
          e.description?.toLowerCase().includes(q)
        );
      }
      setEntries(filtered);

      // Calculate stats from entries
      const totalDebit = filtered.reduce((sum, e) => sum + (e.total_debit || 0), 0);
      const totalCredit = filtered.reduce((sum, e) => sum + (e.total_credit || 0), 0);
      setStats({
        total: entriesData.pagination?.total_count || entriesData.total || filtered.length,
        totalDebit,
        totalCredit,
        isBalanced: trialData.totals?.is_balanced ?? true
      });

      if (accountsData.code === 0) {
        setAccounts(accountsData.accounts || []);
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, entryType, accountFilter, searchQuery]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleExportCSV = async () => {
    let url = `${API_URL}/api/journal-entries/export/csv`;
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (entryType) params.append('entry_type', entryType);
    if (params.toString()) url += `?${params.toString()}`;

    window.open(url, '_blank');
  };

  const [showTallyModal, setShowTallyModal] = useState(false);
  const [tallyDateFrom, setTallyDateFrom] = useState(() => {
    const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-01`;
  });
  const [tallyDateTo, setTallyDateTo] = useState(() => {
    const d = new Date(); return d.toISOString().split('T')[0];
  });
  const [exportingTally, setExportingTally] = useState(false);

  const handleExportTally = async () => {
    setExportingTally(true);
    try {
      const token = localStorage.getItem('token');
      const orgId = localStorage.getItem('organization_id');
      const res = await fetch(
        `${API_URL}/api/finance/export/tally-xml?date_from=${tallyDateFrom}&date_to=${tallyDateTo}`,
        { headers: { Authorization: `Bearer ${token}`, 'X-Organization-ID': orgId || '' } }
      );
      if (!res.ok) {
        const err = await res.json();
        alert(err.detail || 'Export failed');
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tally-${tallyDateFrom}-${tallyDateTo}.xml`;
      a.click();
      URL.revokeObjectURL(url);
      setShowTallyModal(false);
    } catch (e) {
      alert('Export failed: ' + e.message);
    } finally {
      setExportingTally(false);
    }
  };

  const entryTypes = [
    'SALES', 'PURCHASE', 'PAYMENT', 'RECEIPT', 
    'EXPENSE', 'PAYROLL', 'DEPRECIATION', 'JOURNAL'
  ];

  return (
    <div style={{ 
      minHeight: '100vh',
      background: colors.pageBg,
      padding: '32px'
    }} data-testid="journal-entries-page">
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 style={{ 
              fontFamily: 'Syne, sans-serif',
              fontSize: '28px',
              fontWeight: 700,
              color: colors.white,
              margin: '0 0 8px 0'
            }}>
              Journal Ledger
            </h1>
            <p style={{ 
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '12px',
              color: colors.muted,
              margin: 0,
              lineHeight: 1.6
            }}>
              Complete double-entry record of all<br />financial transactions
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            data-testid="new-journal-entry-btn"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 20px',
              background: colors.volt,
              border: 'none',
              borderRadius: '4px',
              color: colors.pageBg,
              fontFamily: 'Syne, sans-serif',
              fontSize: '13px',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            <Plus size={16} />
            New Journal Entry
          </button>
        </div>
      </div>

      {/* Stats Strip */}
      <div style={{ 
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '1px',
        background: colors.border,
        borderRadius: '4px',
        overflow: 'hidden',
        marginBottom: '24px'
      }}>
        <StatCard label="Total Entries" value={stats.total} />
        <StatCard label="Total Debits (Period)" value={stats.totalDebit} format="currency" />
        <StatCard label="Total Credits (Period)" value={stats.totalCredit} format="currency" />
        <StatCard label="Balance Status" value={stats.isBalanced} format="status" />
      </div>

      {/* Tabs */}
      <div style={{ 
        display: 'flex',
        gap: '0',
        marginBottom: '24px',
        borderBottom: `1px solid ${colors.border}`
      }}>
        {[
          { id: 'entries', label: 'Journal Entries' },
          { id: 'ledger', label: 'Account Ledger' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '12px 24px',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === tab.id ? `2px solid ${colors.volt}` : '2px solid transparent',
              color: activeTab === tab.id ? colors.volt : colors.muted,
              fontFamily: 'Syne, sans-serif',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
              marginBottom: '-1px'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'entries' ? (
        <>
          {/* Filter Bar */}
          <div style={{ 
            display: 'flex',
            gap: '12px',
            marginBottom: '24px',
            padding: '16px 20px',
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: '4px',
            flexWrap: 'wrap'
          }}>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <Calendar size={14} style={{ color: colors.muted }} />
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                placeholder="From"
                style={{
                  padding: '8px 12px',
                  background: colors.pageBg,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  color: colors.white,
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '12px',
                  width: '140px'
                }}
              />
              <span style={{ color: colors.muted }}>—</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                placeholder="To"
                style={{
                  padding: '8px 12px',
                  background: colors.pageBg,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  color: colors.white,
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '12px',
                  width: '140px'
                }}
              />
            </div>
            
            <select
              value={entryType}
              onChange={(e) => setEntryType(e.target.value)}
              style={{
                padding: '8px 12px',
                background: colors.pageBg,
                border: `1px solid ${colors.border}`,
                borderRadius: '4px',
                color: colors.white,
                fontSize: '12px',
                minWidth: '140px'
              }}
            >
              <option value="">All Types</option>
              {entryTypes.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>

            <select
              value={accountFilter}
              onChange={(e) => setAccountFilter(e.target.value)}
              style={{
                padding: '8px 12px',
                background: colors.pageBg,
                border: `1px solid ${colors.border}`,
                borderRadius: '4px',
                color: colors.white,
                fontSize: '12px',
                minWidth: '200px'
              }}
            >
              <option value="">All Accounts</option>
              {accounts.map(acc => (
                <option key={acc.account_id} value={acc.account_id}>
                  {acc.account_code} - {acc.account_name}
                </option>
              ))}
            </select>

            <div style={{ position: 'relative', flex: 1, minWidth: '200px' }}>
              <Search size={14} style={{ 
                position: 'absolute', 
                left: '12px', 
                top: '50%', 
                transform: 'translateY(-50%)',
                color: colors.muted 
              }} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search ref no. or description..."
                style={{
                  width: '100%',
                  padding: '8px 12px 8px 36px',
                  background: colors.pageBg,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  color: colors.white,
                  fontSize: '12px'
                }}
              />
            </div>

            <button
              onClick={handleExportCSV}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                background: 'transparent',
                border: `1px solid ${colors.border}`,
                borderRadius: '4px',
                color: colors.muted,
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '11px',
                cursor: 'pointer'
              }}
            >
              <Download size={14} />
              Export CSV
            </button>

            <button
              onClick={() => setShowTallyModal(true)}
              data-testid="export-tally-btn"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                background: 'rgb(var(--bw-volt) / 0.06)',
                border: '1px solid rgba(200,255,0,0.25)',
                borderRadius: '4px',
                color: colors.volt,
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '11px',
                cursor: 'pointer',
                letterSpacing: '0.05em'
              }}
            >
              <Download size={14} />
              Export to Tally
            </button>

            {/* Tally Export Modal */}
            {showTallyModal && (
              <div style={{
                position: 'fixed', inset: 0, zIndex: 1000,
                background: 'rgba(0,0,0,0.65)',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>
                <div style={{
                  background: colors.cardBg,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '8px',
                  padding: '24px',
                  width: '400px',
                  maxWidth: '90vw',
                }}>
                  <h3 style={{ fontFamily: 'Syne, sans-serif', fontSize: '16px', color: colors.white, margin: '0 0 16px 0' }}>
                    Export to Tally XML
                  </h3>
                  <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ fontSize: '11px', color: colors.muted, display: 'block', marginBottom: '4px' }}>FROM</label>
                      <input type="date" value={tallyDateFrom} onChange={e => setTallyDateFrom(e.target.value)}
                        style={{ width: '100%', padding: '8px', background: colors.pageBg, border: `1px solid ${colors.border}`, borderRadius: '4px', color: colors.white, fontSize: '12px' }}
                      />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={{ fontSize: '11px', color: colors.muted, display: 'block', marginBottom: '4px' }}>TO</label>
                      <input type="date" value={tallyDateTo} onChange={e => setTallyDateTo(e.target.value)}
                        style={{ width: '100%', padding: '8px', background: colors.pageBg, border: `1px solid ${colors.border}`, borderRadius: '4px', color: colors.white, fontSize: '12px' }}
                      />
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                    <button onClick={() => setShowTallyModal(false)}
                      style={{ padding: '8px 16px', background: 'transparent', border: `1px solid ${colors.border}`, borderRadius: '4px', color: colors.muted, fontSize: '12px', cursor: 'pointer' }}>
                      Cancel
                    </button>
                    <button onClick={handleExportTally} disabled={exportingTally}
                      style={{ padding: '8px 16px', background: colors.volt, border: 'none', borderRadius: '4px', color: colors.pageBg, fontSize: '12px', fontWeight: 700, cursor: 'pointer' }}>
                      {exportingTally ? 'Generating…' : 'Download XML'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Entries Table */}
          <div style={{ 
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'rgb(255 255 255 / 0.03)' }}>
                  {['Date', 'Ref No.', 'Type', 'Description', 'Source Doc', 'Debit ₹', 'Credit ₹', 'Status', ''].map(h => (
                    <th key={h} style={{ 
                      padding: '12px 16px',
                      textAlign: h.includes('₹') ? 'right' : 'left',
                      fontFamily: 'JetBrains Mono, monospace',
                      fontSize: '10px',
                      textTransform: 'uppercase',
                      color: colors.muted,
                      fontWeight: 500,
                      letterSpacing: '0.5px',
                      whiteSpace: 'nowrap'
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="9" style={{ padding: '40px', textAlign: 'center', color: colors.muted }}>
                      Loading...
                    </td>
                  </tr>
                ) : entries.length === 0 ? (
                  <tr>
                    <td colSpan="9" style={{ padding: '40px', textAlign: 'center', color: colors.muted }}>
                      No journal entries found
                    </td>
                  </tr>
                ) : entries.map(entry => (
                  <React.Fragment key={entry.entry_id}>
                    <tr 
                      style={{ 
                        borderBottom: `1px solid ${colors.border}`,
                        background: expandedEntry === entry.entry_id ? 'rgba(200,255,0,0.03)' : 'transparent',
                        cursor: 'pointer'
                      }}
                      onClick={() => setExpandedEntry(expandedEntry === entry.entry_id ? null : entry.entry_id)}
                    >
                      <td style={{ 
                        padding: '14px 16px',
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: '12px',
                        color: colors.muted
                      }}>
                        {entry.entry_date}
                      </td>
                      <td style={{ 
                        padding: '14px 16px',
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: '12px',
                        color: colors.volt
                      }}>
                        {entry.reference_number}
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <EntryTypePill type={entry.entry_type} />
                      </td>
                      <td style={{ 
                        padding: '14px 16px',
                        fontFamily: 'Syne, sans-serif',
                        fontSize: '13px',
                        color: colors.white,
                        maxWidth: '250px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>
                        {entry.description}
                      </td>
                      <td style={{ 
                        padding: '14px 16px',
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: '12px',
                        color: entry.source_document_id ? colors.blue : colors.muted
                      }}>
                        {entry.source_document_type ? `${entry.source_document_type.toUpperCase()}` : '—'}
                      </td>
                      <td style={{ 
                        padding: '14px 16px',
                        textAlign: 'right',
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: '13px',
                        color: colors.white,
                        fontWeight: 700
                      }}>
                        {formatCurrency(entry.total_debit)}
                      </td>
                      <td style={{ 
                        padding: '14px 16px',
                        textAlign: 'right',
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: '13px',
                        color: colors.white,
                        fontWeight: 700
                      }}>
                        {formatCurrency(entry.total_credit)}
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <StatusPill status={entry.is_posted ? 'posted' : 'draft'} />
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        {expandedEntry === entry.entry_id ? (
                          <ChevronDown size={16} style={{ color: colors.volt }} />
                        ) : (
                          <ChevronRight size={16} style={{ color: colors.muted }} />
                        )}
                      </td>
                    </tr>
                    {expandedEntry === entry.entry_id && (
                      <tr>
                        <td colSpan="9" style={{ padding: '0 16px 16px 16px' }}>
                          <EntryLines lines={entry.lines || []} />
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <AccountLedgerTab accounts={accounts} />
      )}

      {/* Modal */}
      <JournalEntryModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        accounts={accounts}
        onSuccess={fetchData}
      />
    </div>
  );
};

export default JournalEntries;
