import { useState } from "react";

/**
 * useEstimateFilters
 *
 * Manages the list-view filter state for the Estimates page.
 * Filtering is server-side: these values are appended to the API request URL
 * by the parent component. No API calls live here.
 *
 * @returns {{
 *   search: string,
 *   setSearch: Function,
 *   statusFilter: string,
 *   setStatusFilter: Function,
 * }}
 */
export function useEstimateFilters() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  return {
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
  };
}
