import dayjs from 'dayjs';
import { useCallback } from 'react';

import Chip from '@mui/material/Chip';

import { fDateShortLabel } from 'src/utils/format-time';

import { chipProps, FiltersBlock, FiltersResult } from 'src/components/filters-result';

// ----------------------------------------------------------------------

export function ShipmentTableFiltersResultListSkuHistory({ filters, totalResults, onResetPage, sx }) {
  const handleRemoveKeyword = useCallback(() => {
    onResetPage();
    filters.setState({ sku: '' });
  }, [filters, onResetPage]);

  const handleRemoveDate = useCallback((nameDate) => {
    onResetPage();
    const date = dayjs().toISOString();
    filters.setState((prev) => ({
      ...prev,
      [nameDate]: dayjs(date),
    }));
  }, [filters, onResetPage]);

  const handleReset = useCallback(() => {
    onResetPage();
    filters.onResetState();
    const date = dayjs().toISOString();
    filters.setState({ endDate: dayjs(date), startDate: dayjs(date) });
  }, [filters, onResetPage]);

  return (
    <FiltersResult totalResults={totalResults} onReset={handleReset} sx={sx}>

      <FiltersBlock
        label="Start Date:"
        isShow={Boolean(filters.state.startDate)}
      >
        <Chip
          {...chipProps}
          label={fDateShortLabel(filters.state.startDate)}
          onDelete={() => handleRemoveDate('startDate')}
        />
      </FiltersBlock>

      <FiltersBlock
        label="End Date:"
        isShow={Boolean(filters.state.endDate)}
      >
        <Chip
          {...chipProps}
          label={fDateShortLabel(filters.state.endDate)}
          onDelete={() => handleRemoveDate('endDate')}
        />
      </FiltersBlock>

      <FiltersBlock label="Keyword:" isShow={!!filters.state.sku}>
        <Chip {...chipProps} label={filters.state.sku} onDelete={handleRemoveKeyword} />
      </FiltersBlock>
    </FiltersResult>
  );
}
