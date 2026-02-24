/**
 * Indian Financial Year utilities (April 1 - March 31)
 */

export const getIndianFinancialYear = (date = new Date()) => {
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const fyStartYear = month >= 4 ? year : year - 1;
  const fyEndYear = fyStartYear + 1;
  return {
    start: new Date(fyStartYear, 3, 1),
    end: new Date(fyEndYear, 2, 31),
    label: `FY ${fyStartYear}-${String(fyEndYear).slice(2)}`,
  };
};

export const getCurrentFYStart = () => getIndianFinancialYear().start;
export const getCurrentFYEnd = () => getIndianFinancialYear().end;
export const getCurrentFYLabel = () => getIndianFinancialYear().label;
