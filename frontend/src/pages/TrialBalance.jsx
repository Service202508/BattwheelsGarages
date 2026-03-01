import React, { useState, useEffect, useCallback } from 'react';
import { Download, Calendar, FileText, Check, X, AlertTriangle } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Design tokens
const colors = {
  pageBg: '#0D1317',
  cardBg: '#111820',
  border: 'rgba(255,255,255,0.07)',
  volt: '#C8FF00',
  voltDim: 'rgba(200,255,0,0.08)',
  voltBorder: 'rgba(200,255,0,0.25)',
  white: '#F4F6F0',
  muted: 'rgba(244,246,240,0.45)',
  green: '#22C55E',
  greenBg: 'rgba(34,197,94,0.08)',
  greenBorder: 'rgba(34,197,94,0.25)',
  red: '#FF3B2F',
  redBg: 'rgba(255,59,47,0.08)',
  redBorder: 'rgba(255,59,47,0.25)',
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

// Account type order for grouping
const accountTypeOrder = ['Asset', 'Liability', 'Equity', 'Income', 'Expense'];

const TrialBalance = () => {
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0]);
  const [trialData, setTrialData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchTrialBalance = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/api/journal-entries/reports/trial-balance?as_of_date=${asOfDate}`,
        {
          headers: { 'X-Organization-ID': 'default' },
          credentials: 'include'
        }
      );
      const data = await response.json();
      if (data.code === 0) {
        setTrialData(data);
      }
    } catch (err) {
      console.error('Error fetching trial balance:', err);
    } finally {
      setLoading(false);
    }
  }, [asOfDate]);

  useEffect(() => {
    fetchTrialBalance();
  }, [fetchTrialBalance]);

  // Group accounts by type
  const groupedAccounts = React.useMemo(() => {
    if (!trialData?.accounts) return {};
    
    const grouped = {};
    accountTypeOrder.forEach(type => {
      grouped[type] = {
        accounts: [],
        totalDebit: 0,
        totalCredit: 0
      };
    });

    trialData.accounts.forEach(acc => {
      const type = acc.account_type;
      if (grouped[type]) {
        grouped[type].accounts.push(acc);
        grouped[type].totalDebit += acc.debit_balance || 0;
        grouped[type].totalCredit += acc.credit_balance || 0;
      }
    });

    return grouped;
  }, [trialData]);

  const handleExportCSV = () => {
    window.open(`${API_URL}/api/journal-entries/reports/trial-balance/csv?as_of_date=${asOfDate}`, '_blank');
  };

  const isBalanced = trialData?.totals?.is_balanced ?? true;
  const difference = trialData?.totals?.difference ?? 0;

  return (
    <div style={{ 
      minHeight: '100vh',
      background: colors.pageBg,
      padding: '32px'
    }} data-testid="trial-balance-page">
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
              Trial Balance
            </h1>
            <p style={{ 
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '12px',
              color: colors.muted,
              margin: 0
            }}>
              Verify that total debits equal total credits
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Calendar size={14} style={{ color: colors.muted }} />
              <span style={{ 
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '11px',
                color: colors.muted,
                textTransform: 'uppercase'
              }}>
                As of
              </span>
              <input
                type="date"
                value={asOfDate}
                onChange={(e) => setAsOfDate(e.target.value)}
                style={{
                  padding: '8px 12px',
                  background: colors.cardBg,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  color: colors.white,
                  fontFamily: 'JetBrains Mono, monospace',
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
          </div>
        </div>
      </div>

      {/* Balance Status Banner */}
      <div style={{
        background: isBalanced ? colors.greenBg : colors.redBg,
        border: `1px solid ${isBalanced ? colors.greenBorder : colors.redBorder}`,
        borderRadius: '4px',
        padding: '16px 24px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      }}>
        {isBalanced ? (
          <>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: colors.greenBorder,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Check size={18} style={{ color: colors.green }} />
            </div>
            <div>
              <div style={{ 
                fontFamily: 'Syne, sans-serif',
                fontSize: '15px',
                fontWeight: 700,
                color: colors.green
              }}>
                ✓ Trial Balance is BALANCED as of {asOfDate}
              </div>
              <div style={{ 
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '11px',
                color: colors.muted,
                marginTop: '4px'
              }}>
                Total Debits: {formatCurrency(trialData?.totals?.total_debit || 0)} = Total Credits: {formatCurrency(trialData?.totals?.total_credit || 0)}
              </div>
            </div>
          </>
        ) : (
          <>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: colors.redBorder,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <AlertTriangle size={18} style={{ color: colors.red }} />
            </div>
            <div>
              <div style={{ 
                fontFamily: 'Syne, sans-serif',
                fontSize: '15px',
                fontWeight: 700,
                color: colors.red
              }}>
                ✗ Trial Balance is OUT OF BALANCE
              </div>
              <div style={{ 
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '12px',
                color: colors.red,
                marginTop: '4px'
              }}>
                Difference: {formatCurrency(Math.abs(difference))} — Review journal entries for errors
              </div>
            </div>
          </>
        )}
      </div>

      {/* Trial Balance Table */}
      <div style={{ 
        background: colors.cardBg,
        border: `1px solid ${colors.border}`,
        borderRadius: '4px',
        overflow: 'hidden'
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'rgb(255 255 255 / 0.03)' }}>
              <th style={{ 
                padding: '14px 20px',
                textAlign: 'left',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '10px',
                textTransform: 'uppercase',
                color: colors.muted,
                fontWeight: 500,
                letterSpacing: '0.5px',
                width: '100px'
              }}>Account Code</th>
              <th style={{ 
                padding: '14px 20px',
                textAlign: 'left',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '10px',
                textTransform: 'uppercase',
                color: colors.muted,
                fontWeight: 500,
                letterSpacing: '0.5px'
              }}>Account Name</th>
              <th style={{ 
                padding: '14px 20px',
                textAlign: 'right',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '10px',
                textTransform: 'uppercase',
                color: colors.muted,
                fontWeight: 500,
                letterSpacing: '0.5px',
                width: '150px'
              }}>Debit ₹</th>
              <th style={{ 
                padding: '14px 20px',
                textAlign: 'right',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '10px',
                textTransform: 'uppercase',
                color: colors.muted,
                fontWeight: 500,
                letterSpacing: '0.5px',
                width: '150px'
              }}>Credit ₹</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="4" style={{ padding: '40px', textAlign: 'center', color: colors.muted }}>
                  Loading...
                </td>
              </tr>
            ) : (
              accountTypeOrder.map(accountType => {
                const group = groupedAccounts[accountType];
                if (!group || group.accounts.length === 0) return null;

                return (
                  <React.Fragment key={accountType}>
                    {/* Group Header */}
                    <tr style={{ background: 'rgba(255,255,255,0.02)' }}>
                      <td colSpan="4" style={{ 
                        padding: '12px 20px',
                        fontFamily: 'Syne, sans-serif',
                        fontSize: '12px',
                        fontWeight: 700,
                        color: colors.volt,
                        textTransform: 'uppercase',
                        letterSpacing: '1px',
                        borderTop: `1px solid ${colors.border}`
                      }}>
                        {accountType}S
                      </td>
                    </tr>
                    
                    {/* Account Rows */}
                    {group.accounts.map(account => (
                      <tr key={account.account_id} style={{ borderBottom: `1px solid ${colors.border}` }}>
                        <td style={{ 
                          padding: '12px 20px',
                          fontFamily: 'JetBrains Mono, monospace',
                          fontSize: '12px',
                          color: colors.volt
                        }}>
                          {account.account_code}
                        </td>
                        <td style={{ 
                          padding: '12px 20px',
                          fontFamily: 'Syne, sans-serif',
                          fontSize: '13px',
                          color: colors.white
                        }}>
                          {account.account_name}
                        </td>
                        <td style={{ 
                          padding: '12px 20px',
                          textAlign: 'right',
                          fontFamily: 'JetBrains Mono, monospace',
                          fontSize: '13px',
                          color: account.debit_balance > 0 ? colors.white : colors.muted
                        }}>
                          {account.debit_balance > 0 ? formatCurrency(account.debit_balance) : '—'}
                        </td>
                        <td style={{ 
                          padding: '12px 20px',
                          textAlign: 'right',
                          fontFamily: 'JetBrains Mono, monospace',
                          fontSize: '13px',
                          color: account.credit_balance > 0 ? colors.white : colors.muted
                        }}>
                          {account.credit_balance > 0 ? formatCurrency(account.credit_balance) : '—'}
                        </td>
                      </tr>
                    ))}
                    
                    {/* Group Subtotal */}
                    <tr style={{ background: 'rgba(255,255,255,0.04)' }}>
                      <td colSpan="2" style={{ 
                        padding: '10px 20px',
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: '11px',
                        color: colors.muted,
                        textAlign: 'right',
                        fontWeight: 700
                      }}>
                        {accountType.toUpperCase()} SUBTOTAL
                      </td>
                      <td style={{ 
                        padding: '10px 20px',
                        textAlign: 'right',
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: '13px',
                        color: colors.white,
                        fontWeight: 700
                      }}>
                        {group.totalDebit > 0 ? formatCurrency(group.totalDebit) : '—'}
                      </td>
                      <td style={{ 
                        padding: '10px 20px',
                        textAlign: 'right',
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: '13px',
                        color: colors.white,
                        fontWeight: 700
                      }}>
                        {group.totalCredit > 0 ? formatCurrency(group.totalCredit) : '—'}
                      </td>
                    </tr>
                  </React.Fragment>
                );
              })
            )}
          </tbody>
          
          {/* Grand Total */}
          {!loading && trialData && (
            <tfoot>
              <tr style={{ 
                background: colors.voltDim,
                borderTop: `2px solid ${colors.voltBorder}`
              }}>
                <td colSpan="2" style={{ 
                  padding: '16px 20px',
                  fontFamily: 'Syne, sans-serif',
                  fontSize: '14px',
                  fontWeight: 700,
                  color: colors.volt,
                  textAlign: 'right'
                }}>
                  GRAND TOTAL
                </td>
                <td style={{ 
                  padding: '16px 20px',
                  textAlign: 'right',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '16px',
                  fontWeight: 700,
                  color: colors.volt
                }}>
                  {formatCurrency(trialData.totals?.total_debit || 0)}
                </td>
                <td style={{ 
                  padding: '16px 20px',
                  textAlign: 'right',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '16px',
                  fontWeight: 700,
                  color: colors.volt
                }}>
                  {formatCurrency(trialData.totals?.total_credit || 0)}
                </td>
              </tr>
              
              {/* Balance check row */}
              <tr style={{ background: isBalanced ? colors.greenBg : colors.redBg }}>
                <td colSpan="4" style={{ 
                  padding: '12px 20px',
                  textAlign: 'center',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '13px',
                  fontWeight: 700,
                  color: isBalanced ? colors.green : colors.red
                }}>
                  {isBalanced 
                    ? '✓ DEBITS = CREDITS — TRIAL BALANCE VERIFIED' 
                    : `✗ DIFFERENCE: ${formatCurrency(Math.abs(difference))} — REQUIRES INVESTIGATION`
                  }
                </td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>

      {/* Summary Cards */}
      {!loading && trialData && (
        <div style={{ 
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '16px',
          marginTop: '24px'
        }}>
          <div style={{
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: '4px',
            padding: '20px'
          }}>
            <div style={{ 
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '10px',
              textTransform: 'uppercase',
              color: colors.muted,
              marginBottom: '8px'
            }}>
              Total Accounts
            </div>
            <div style={{ 
              fontFamily: 'Syne, sans-serif',
              fontSize: '24px',
              fontWeight: 700,
              color: colors.volt
            }}>
              {trialData.accounts?.length || 0}
            </div>
          </div>
          
          <div style={{
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: '4px',
            padding: '20px'
          }}>
            <div style={{ 
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '10px',
              textTransform: 'uppercase',
              color: colors.muted,
              marginBottom: '8px'
            }}>
              With Debit Balance
            </div>
            <div style={{ 
              fontFamily: 'Syne, sans-serif',
              fontSize: '24px',
              fontWeight: 700,
              color: colors.green
            }}>
              {trialData.accounts?.filter(a => a.debit_balance > 0).length || 0}
            </div>
          </div>
          
          <div style={{
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: '4px',
            padding: '20px'
          }}>
            <div style={{ 
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '10px',
              textTransform: 'uppercase',
              color: colors.muted,
              marginBottom: '8px'
            }}>
              With Credit Balance
            </div>
            <div style={{ 
              fontFamily: 'Syne, sans-serif',
              fontSize: '24px',
              fontWeight: 700,
              color: 'rgb(var(--bw-blue))'
            }}>
              {trialData.accounts?.filter(a => a.credit_balance > 0).length || 0}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrialBalance;
