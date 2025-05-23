import axios from 'axios';
import React, { useRef, useMemo, useState, useEffect, useContext, useCallback } from 'react';

import Grid from '@mui/material/Unstable_Grid2';
import Typography from '@mui/material/Typography';
import { Box, Card, Stack, Table, Alert, TableRow, TableBody, TableCell, CardHeader, TableContainer, LinearProgress } from '@mui/material';

import { paths } from 'src/routes/paths';
import { useRouter } from 'src/routes/hooks';

import { useSetState } from 'src/hooks/use-set-state';

import { fDateTime } from 'src/utils/format-time';

import { CONFIG } from 'src/config-global';
import { DashboardContent } from 'src/layouts/dashboard';

import { Label } from 'src/components/label';
import MatchGauge from 'src/components/chart/gauge-chart';
import AnimatedIcon from 'src/components/animate/animated-icon';
import { useTable, TableNoData, getComparator } from 'src/components/table';

import { ItemListShortView } from 'src/sections/item/view';
import { WelcomeTypography } from 'src/sections/welcome-typography/welcome-typography';

import { LoadingContext } from 'src/auth/context/loading-context';
import { useDataContext } from 'src/auth/context/data/data-context';

import { ModalSublistItems } from './modal-sublist-items';
import { ModalListItemsSerials } from './modal-list-items-serials';
import { AnalyticsOrderTimeline } from '../analytics-order-timeline';
import { AnalyticsWidgetSummary } from '../analytics-widget-summary';
import { AnalyticsCurrentVisits } from '../analytics-current-visits';


const headersCSV = [
  { label: 'SKU', key: 'sku' },
  { label: 'Qty', key: 'stockOnHand' },
  { label: 'Difference', key: 'difference' },
]

// ----------------------------------------------------------------------

export function OverviewAnalyticsView() {


  const { setError, isMobile } = useContext(LoadingContext);

  const [updating, setUpdating] = useState(false);

  const [titleLinearProgress, setTitleLinearProgress] = useState('Loading data...');

  const router = useRouter();

  const [categories, setCategories] = useState(['Items']);

  const [openModal, setOpenModal] = useState({
    subListItems: false,
    subListItemsSerials: false,
    itemSerialsDetails: false,
    listItemsSerials: false,
  });

  const handleOpenModal = (modalId) => {
    setOpenModal((prev) => ({ ...prev, [modalId]: true }));
  };

  const handleCloseModal = (modalId) => {
    setOpenModal((prev) => ({ ...prev, [modalId]: false }));
  };

  const [modalListItems, setModalListItems] = useState(null);
  const [modalTitle, setModalTitle] = useState(null);
  const [modalButtonColor, setModalButtonColor] = useState(null);

  const filters = useSetState({ name: '' });

  const table = useTable({ defaultDense: true });

  const itemsZohoSenitronRef = useRef(null);

  const intervalIdRef = useRef(null);

  const userLogged = useMemo(() => JSON.parse(localStorage.getItem('userLogged')), []);

  const [hasIgnoredErrors, setHasIgnoredErrors] = useState(false);

  // console.log('userLogged', userLogged);

  const {
    senitronItems,
    timelineItems,
    itemsZohoData,
    itemsTimelineData,
    itemsSkuTrackInfo,
    jobsUpdatingTimeData,
    manualUpdatingJobsData,
    itemsAssetsLogsInfo,
    itemsZohoSenitron,
    itemsSenitronZoho,
    countLostItems,
  } = useDataContext();


  const itemsSynced = useMemo(() => {
    if (itemsZohoData) {
      return itemsZohoData.filter((item) => item.syncedWithSenitron);
    }
    return null;
  }, [itemsZohoData]);

  const totalSenitronQty = useMemo(() => {
    if (senitronItems) {
      return senitronItems.reduce((acc, senitronItem) => acc + senitronItem.count, 0);
    }
    return null;
  }, [senitronItems]);

  const totalZohoQty = useMemo(() => {
    if (itemsSynced) {
      return itemsSynced.reduce((acc, item) => acc + item.stockOnHand, 0);
    }
    return null;
  }, [itemsSynced]);


  const itemsIgnoreErrors = useMemo(() => {
    if (itemsZohoSenitron) {
      return itemsZohoSenitron.filter((item) => item.syncedWithSenitron && item.ignoreErrors);
    }
    return null;
  }, [itemsZohoSenitron]);


  const { series, seriesPieChart } = useMemo(() => {
    if (itemsZohoSenitron && itemsSenitronZoho) {
      const itemsSync = itemsZohoSenitron.filter((item) => item.syncedWithSenitron);
      const sseries = itemsSync.map((item) => {
        const senitronItem = itemsSenitronZoho?.find(
          (sItem) => sItem.itemNumber === item.itemId
        );
        const zohoQty = item?.stockOnHand || 0;
        const senitronQty = senitronItem?.count || 0;
        const max = Math.max(zohoQty, senitronQty);
        const min = Math.min(zohoQty, senitronQty);
        const match = max !== 0 ? Math.floor((min / max) * 100) : max === 0 && min === 0 ? 100 : 0;
        return match;
      });
      const sseriesAvg = processingNumbers(sseries);
      const pieChart = processingNumbersPieChart(sseries);
      return { series: sseriesAvg, seriesPieChart: pieChart };
    }
    return { series: null, seriesPieChart: null };
  }, [itemsZohoSenitron, itemsSenitronZoho]);


  const { percentage, totalErrors } = useMemo(() => {
    if (itemsZohoSenitron) {
      const errors =
        Math.abs(
          parseInt(
            itemsZohoSenitron
              ?.filter(
                (it) =>
                  parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) > 0 &&
                  it.syncedWithSenitron &&
                  !it.ignoreErrors
              )
              .reduce((acc, it) => acc + it.quantity, 0),
            10
          ) -
          parseInt(
            itemsZohoSenitron
              ?.filter(
                (it) =>
                  parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) > 0 &&
                  it.syncedWithSenitron &&
                  !it.ignoreErrors
              )
              .reduce((acc, it) => acc + it.stockOnHand, 0),
            10
          )
        ) +
        Math.abs(
          parseInt(
            itemsZohoSenitron
              ?.filter(
                (it) =>
                  parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) < 0 &&
                  it.syncedWithSenitron &&
                  !it.ignoreErrors
              )
              .reduce((acc, it) => acc + it.quantity, 0),
            10
          ) -
          parseInt(
            itemsZohoSenitron
              ?.filter(
                (it) =>
                  parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) < 0 &&
                  it.syncedWithSenitron &&
                  !it.ignoreErrors
              )
              .reduce((acc, it) => acc + it.stockOnHand, 0),
            10
          )
        );

      const tSenitronQty = itemsZohoSenitron
        ?.filter((it) => it.syncedWithSenitron && !it.ignoreErrors)
        .reduce((acc, item) => acc + item.quantity, 0);

      const tOnHand = itemsZohoSenitron
        ?.filter((it) => it.syncedWithSenitron && !it.ignoreErrors)
        .reduce((acc, item) => acc + item.stockOnHand, 0);

      const tErrors = errors;
      const tRFIDCorrect = tSenitronQty - errors;
      const percent = Math.floor(((tOnHand - errors) / tOnHand) * 100) || 0;
      return { percentage: percent, totalErrors: tErrors, totalRFIDCorrect: tRFIDCorrect };
    }
    return { percentage: null, totalErrors: null, totalRFIDCorrect: null };
  }, [itemsZohoSenitron]);

  /**
   * Shipments
   */

  // console.log('finalGroupedArray', finalGroupedArray);

  // Data loaded validation

  const [dataLoaded, setDataLoaded] = useState(false);

  useEffect(() => {
    if (
      itemsZohoSenitron &&
      itemsSenitronZoho &&
      itemsTimelineData &&
      itemsZohoData &&
      seriesPieChart &&
      totalZohoQty !== null &&
      totalSenitronQty !== null &&
      totalErrors !== null &&
      !updating
    ) {
      setDataLoaded(true);
    } else {
      setDataLoaded(false);
    }
  }, [
    itemsZohoSenitron,
    itemsSenitronZoho,
    itemsTimelineData,
    itemsZohoData,
    seriesPieChart,
    totalZohoQty,
    totalSenitronQty,
    totalErrors,
    updating,
  ]);

  useEffect(() => {
    if (itemsZohoSenitron) {
      itemsZohoSenitronRef.current = itemsZohoSenitron;
    }
  }, [itemsZohoSenitron]);

  useEffect(() => {
    async function createZohoSenitronItems() {
      const currentItems = itemsZohoSenitronRef.current;
      if (currentItems) {
        try {
          // console.log('response', response);
        } catch (err) {
          console.error('Error al crear la información de seguimiento de SKU:', err);
        }
      }
    }

    if (dataLoaded && !intervalIdRef.current) {
      createZohoSenitronItems();
      intervalIdRef.current = setInterval(() => {
        createZohoSenitronItems();
      }, 5 * 60 * 1000);
    }

    return () => {
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    };
  }, [dataLoaded]);


  const modalDataFiltered = applyFilter({
    inputData: modalListItems,
    comparator: getComparator(table.order, table.orderBy),
    filters: filters.state,
  });


  const handleFilterName = useCallback(
    (event) => {
      filters.setState({ name: event.target.value });
    },
    [filters]
  );

  const handleViewRow = useCallback(
    (id) => {
      localStorage.removeItem('routeByOrder');
      localStorage.removeItem('routeByShipment');
      localStorage.removeItem('routeByShipmentBySku');
      localStorage.setItem('routeByAnalytics', id);
      router.push(paths.dashboard.item.details(id));
    },
    [router]
  );

  const [ignoreErrorsSelected, setIgnoreErrorsSelected] = React.useState([]);

  const [valueIgnoreErrors, setValueIgnoreErrors] = React.useState(false);

  const [isIgnore, setIsIgnore] = React.useState(true);

  const handleSelectAllIgnoreErrors = () => {
    if (ignoreErrorsSelected.length === modalDataFiltered.length) {
      setIgnoreErrorsSelected([]);
    } else {
      const allItemIds = modalDataFiltered.map((item) => item.itemId);
      setIgnoreErrorsSelected(allItemIds);
    }
  };

  const handleCheckboxChange = (event, itemId) => {
    if (event.target.checked) {
      setIgnoreErrorsSelected((prev) => [...prev, itemId]);
    } else {
      setIgnoreErrorsSelected((prev) => prev.filter((id) => id !== itemId));
    }
  };

  const handleUpdateIgnoreErrors = () => {
    const payload = {
      errors: ignoreErrorsSelected,
      new_value: valueIgnoreErrors,
    };
    axios
      .post(`${CONFIG.apiUrl}/api_zoho/ignore_selected_errors_zoho_items/`, payload)
      .then(() => {
        console.log('Items updated to ignore errors with value:', valueIgnoreErrors);
        handleCloseModal('subListItems');
        setIgnoreErrorsSelected([]);
      })
      .catch((err) => {
        console.error('Error updating items with ignore errors:', err);
        setError('There was an error updating the items with ignore errors.');
      });
  }


  const handleSetManualUpdatingJobs = (isRunning) => {
    const payload = {
      is_running: isRunning,
    };
    axios
      .post(`${CONFIG.apiUrl}/api_zoho/set_manual_updating_jobs/`, payload)
      .then(() => {
        console.log(`Manual updating jobs set to ${isRunning}`);
      })
      .catch((err) => {
        console.error('Error setting manual updating jobs:', err);
        setError('There was an error setting manual updating jobs.');
      });
  }

  const [updatedCountLostItems, setUpdatedCountLostItems] = useState(countLostItems);

  useEffect(() => {
    setUpdatedCountLostItems(countLostItems);
  }, [countLostItems]);


  return (
    <>
      {!itemsZohoSenitron || !itemsSenitronZoho || !itemsTimelineData ||
        !itemsZohoData || !seriesPieChart || totalZohoQty === null ||
        totalSenitronQty === null || totalErrors === null || updating ? (
        <Box
            sx={{
              width: '350px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '80vh',
              margin: 'auto'
            }}
          >
            <Typography variant="body2" sx={{ mb: 1 }}>
              {titleLinearProgress}
            </Typography>
            <LinearProgress
              key="error"
              sx={{
                mb: 2,
                width: '100%',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: 'black',
                },
                backgroundColor: '#e0e0e0',
              }}
            />
          </Box>
      ) : (
        <>
          <DashboardContent maxWidth="xl">
            {!isMobile ? (
              <Grid container spacing={2}>
                <Grid 
                xs={
                  countLostItems === 0 && itemsIgnoreErrors.length === 0 ? 12 : 
                  (countLostItems === 0 && itemsIgnoreErrors.length > 0) || (countLostItems > 0 && itemsIgnoreErrors.length === 0) ? 9.5 : 8
                } 
                sm={
                  countLostItems === 0 && itemsIgnoreErrors.length === 0 ? 12 : 
                  (countLostItems === 0 && itemsIgnoreErrors.length > 0) || (countLostItems > 0 && itemsIgnoreErrors.length === 0) ? 9.5 : 8
                }
                md={
                  countLostItems === 0 && itemsIgnoreErrors.length === 0 ? 12 : 
                  (countLostItems === 0 && itemsIgnoreErrors.length > 0) || (countLostItems > 0 && itemsIgnoreErrors.length === 0) ? 9.5 : 8
                }
                >
                  <WelcomeTypography
                    userLogged={userLogged}
                    manualUpdatingJobsData={manualUpdatingJobsData}
                    jobsUpdatingTimeData={jobsUpdatingTimeData}
                    itemsZohoSenitron={itemsZohoSenitron}
                    setUpdating={setUpdating}
                    setError={setError}
                    handleSetManualUpdatingJobs={handleSetManualUpdatingJobs}
                    setTitleLinearProgress={setTitleLinearProgress}
                    isMobile={isMobile}
                  />
                </Grid >
                {itemsIgnoreErrors.length > 0 && (
                  <Grid xs={countLostItems === 0 ? 2.5 : 2} sm={countLostItems === 0 ? 2.5 : 2} md={countLostItems === 0 ? 2.5 : 2}>
                    <Alert
                      severity="warning"
                      icon={<AnimatedIcon icon="mdi:alert" color="warning" width="25px" />}
                      sx={{ mb: 2, cursor: 'pointer', p: 1 }}
                      onClick={
                        () => {
                          handleOpenModal('subListItems')
                          setModalListItems(itemsIgnoreErrors)
                          setModalTitle(`SKUs with errors ignored`)
                          setModalButtonColor('warning.main')
                          setHasIgnoredErrors(true)
                          setValueIgnoreErrors(false)
                          setIsIgnore(false)
                        }
                      }>
                      <Typography variant="body2" sx={{ fontSize: '14px' }}>
                        <b>{itemsIgnoreErrors.length}</b> SKUs with errors ignored
                      </Typography>
                    </Alert>
                  </Grid>
                )}
                {updatedCountLostItems > 0 && (
                  <Grid xs={itemsIgnoreErrors.length === 0 ? 2.5 : 2} sm={itemsIgnoreErrors.length === 0 ? 2.5 : 2} md={itemsIgnoreErrors.length === 0 ? 2.5 : 2}>
                    <Alert
                      severity="error"
                      icon={<AnimatedIcon icon="mdi:error" color="error" width="25px" />}
                      sx={{ mb: 2, cursor: 'pointer', p: 1 }}>
                      <Typography variant="body2" sx={{ fontSize: '14px' }}>
                        <b>{updatedCountLostItems}</b> {itemsIgnoreErrors.length === 0 ? `Items lost today ( ${fDateTime(new Date(), 'YYYY-MM-DD HH:mm')} ) ` : `Items lost today`} 
                      </Typography>
                    </Alert>
                  </Grid>
                )}
              </Grid >
            ) : (
              <Grid container spacing={2}>
                <Grid 
                xs={
                  countLostItems === 0 && itemsIgnoreErrors.length === 0 ? 12 : 
                  (countLostItems === 0 && itemsIgnoreErrors.length > 0) || (countLostItems > 0 && itemsIgnoreErrors.length === 0) ? 6 : 4
                } 
                sm={
                  countLostItems === 0 && itemsIgnoreErrors.length === 0 ? 12 : 
                  (countLostItems === 0 && itemsIgnoreErrors.length > 0) || (countLostItems > 0 && itemsIgnoreErrors.length === 0) ? 6 : 4
                }
                md={
                  countLostItems === 0 && itemsIgnoreErrors.length === 0 ? 12 : 
                  (countLostItems === 0 && itemsIgnoreErrors.length > 0) || (countLostItems > 0 && itemsIgnoreErrors.length === 0) ? 6 : 4
                }
                >
                  <WelcomeTypography
                    userLogged={userLogged}
                    manualUpdatingJobsData={manualUpdatingJobsData}
                    jobsUpdatingTimeData={jobsUpdatingTimeData}
                    itemsZohoSenitron={itemsZohoSenitron}
                    setUpdating={setUpdating}
                    setError={setError}
                    handleSetManualUpdatingJobs={handleSetManualUpdatingJobs}
                    setTitleLinearProgress={setTitleLinearProgress}
                    isMobile={isMobile}
                  />
                </Grid >
                {itemsIgnoreErrors.length > 0 && (
                  <Grid xs={countLostItems === 0 ? 6 : 4} sm={countLostItems === 0 ? 6 : 4} md={countLostItems === 0 ? 6 : 4}>
                    <Alert
                      severity="warning"
                      icon={<AnimatedIcon icon="mdi:alert" color="warning" width="25px" />}
                      sx={{ mb: 2, cursor: 'pointer', p: 1 }}
                      onClick={
                        () => {
                          handleOpenModal('subListItems')
                          setModalListItems(itemsIgnoreErrors)
                          setModalTitle(`SKUs with errors ignored`)
                          setModalButtonColor('warning.main')
                          setHasIgnoredErrors(true)
                          setValueIgnoreErrors(false)
                          setIsIgnore(false)
                        }
                      }>
                      <Typography variant="body2" sx={{ fontSize: '14px' }}>
                        <b>{itemsIgnoreErrors.length}</b> ignored
                      </Typography>
                    </Alert>
                  </Grid>
                )}
                {updatedCountLostItems > 0 && (
                  <Grid xs={itemsIgnoreErrors.length === 0 ? 6 : 4} sm={itemsIgnoreErrors.length === 0 ? 6 : 4} md={itemsIgnoreErrors.length === 0 ? 6 : 4}>
                    <Alert
                      severity="error"
                      icon={<AnimatedIcon icon="mdi:error" color="error" width="25px" />}
                      sx={{ mb: 2, cursor: 'pointer', p: 1 }}>
                      <Typography variant="body2" sx={{ fontSize: '14px' }}>
                        <b>{updatedCountLostItems}</b> {itemsIgnoreErrors.length === 0 ? ` lost today at ${fDateTime(new Date(), 'YYYY-MM-DD HH:mm')} ` : ` lost today`} 
                      </Typography>
                    </Alert>
                  </Grid>
                )}
              </Grid >
            )}

            <Grid container spacing={3}>
              <Grid xs={12} sm={6} md={3}>
                <AnalyticsWidgetSummary
                  sx={{ cursor: 'pointer' }}
                  title="SKU Tracked"
                  percent={linearRegresionCalculation(itemsSkuTrackInfo?.map((it) => it.skuTracked))}
                  total={itemsZohoSenitron?.filter(it => it.syncedWithSenitron).length}
                  quantity={itemsZohoSenitron?.filter(it => it.syncedWithSenitron).reduce((acc, item) => acc + item.quantity, 0)}
                  stockOnHand={itemsZohoSenitron?.filter(it => it.syncedWithSenitron).reduce((acc, item) => acc + item.stockOnHand, 0)}
                  errors={totalErrors}
                  color="success"
                  icon={
                    <img alt="icon" src={`${CONFIG.assetsDir}/assets/icons/glass/ic-item-synced.svg`} />
                  }
                  chart={{
                    categories: itemsSkuTrackInfo?.map((it) => fDateTime(it.date)).slice(-8),
                    series: itemsSkuTrackInfo?.map((it) => it.skuTracked).slice(-8),
                  }}
                  onClick={() => {
                    handleOpenModal('subListItems')
                    setModalListItems(itemsZohoSenitron?.filter(it => it.syncedWithSenitron))
                    setModalTitle(`SKUs Tracked`)
                    setModalButtonColor('success.main')
                    setHasIgnoredErrors(false)
                    setValueIgnoreErrors(false)
                  }}
                />
              </Grid>

              <Grid xs={12} sm={6} md={3}>
                <AnalyticsWidgetSummary
                  sx={{ cursor: 'pointer' }}
                  title="SKU Matched 100%"
                  percent={linearRegresionCalculation(itemsSkuTrackInfo?.map((it) => it.skuMatched))}
                  total={itemsZohoSenitron?.filter(it => parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) === 0 && it.syncedWithSenitron).length}
                  quantity={itemsZohoSenitron?.filter(it => parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) === 0 && it.syncedWithSenitron).reduce((acc, it) => acc + it.quantity, 0)}
                  stockOnHand={itemsZohoSenitron?.filter(it => parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) === 0 && it.syncedWithSenitron).reduce((acc, it) => acc + it.stockOnHand, 0)}
                  color="info"
                  icon={
                    <img alt="icon" src={`${CONFIG.assetsDir}/assets/icons/glass/ic-item-zoho.svg`} />
                  }
                  chart={{
                    categories: itemsSkuTrackInfo?.map((it) => fDateTime(it.date)).slice(-8),
                    series: itemsSkuTrackInfo?.map((it) => it.skuMatched).slice(-8),
                  }}
                  onClick={() => {
                    handleOpenModal('subListItems')
                    setModalListItems(itemsZohoSenitron?.filter(it => parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) === 0 && it.syncedWithSenitron))
                    setModalTitle(`SKUs Matched 100%`)
                    // setModalButtonColor('#8E33FF')
                    setModalButtonColor('info.main')
                    setHasIgnoredErrors(false)
                    setValueIgnoreErrors(false)
                  }}
                />
              </Grid>

              <Grid xs={12} sm={6} md={3}>
                <AnalyticsWidgetSummary
                  sx={{ cursor: 'pointer' }}
                  title="SKU Missing Items"
                  percent={linearRegresionCalculation(itemsSkuTrackInfo?.map((it) => it.skuMissing))}
                  total={itemsZohoSenitron?.filter(it => parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) > 0 && it.syncedWithSenitron && !it.ignoreErrors).length}
                  quantity={itemsZohoSenitron?.filter(it => parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) > 0 && it.syncedWithSenitron && !it.ignoreErrors).reduce((acc, it) => acc + it.quantity, 0)}
                  stockOnHand={itemsZohoSenitron?.filter(it => parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) > 0 && it.syncedWithSenitron && !it.ignoreErrors).reduce((acc, it) => acc + it.stockOnHand, 0)}
                  color="error"
                  icon={
                    <img alt="icon" src={`${CONFIG.assetsDir}/assets/icons/glass/ic-item-mismatch.svg`} />
                  }
                  chart={{
                    categories: itemsSkuTrackInfo?.map((it) => fDateTime(it.date)).slice(-8),
                    series: itemsSkuTrackInfo?.map((it) => it.skuMissing).slice(-8),
                  }}
                  onClick={() => {
                    handleOpenModal('subListItems')
                    setModalListItems(itemsZohoSenitron?.filter(it => parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) > 0 && it.syncedWithSenitron && !it.ignoreErrors))
                    setModalTitle(`SKUs with missing Items`)
                    setModalButtonColor('#F44336')
                    setHasIgnoredErrors(true)
                    setValueIgnoreErrors(true)
                    setIsIgnore(true)
                  }}
                />
              </Grid>

              <Grid xs={12} sm={5} md={3}>
                <AnalyticsWidgetSummary
                  sx={{ cursor: 'pointer' }}
                  title="SKU Excess Items"
                  percent={linearRegresionCalculation(itemsSkuTrackInfo?.map((it) => it.skuExcess))}
                  total={itemsZohoSenitron?.filter(it => parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) < 0 && it.syncedWithSenitron && !it.ignoreErrors).length}
                  quantity={itemsZohoSenitron?.filter(it => parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) < 0 && it.syncedWithSenitron && !it.ignoreErrors).reduce((acc, it) => acc + it.quantity, 0)}
                  stockOnHand={itemsZohoSenitron?.filter(it => parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) < 0 && it.syncedWithSenitron && !it.ignoreErrors).reduce((acc, it) => acc + it.stockOnHand, 0)}
                  color="warning"
                  icon={
                    <img alt="icon" src={`${CONFIG.assetsDir}/assets/icons/glass/ic-item-front-3.svg`} />
                  }
                  chart={{
                    categories: itemsSkuTrackInfo?.map((it) => fDateTime(it.date)).slice(-8),
                    series: itemsSkuTrackInfo?.map((it) => it.skuExcess).slice(-8),
                  }}
                  onClick={() => {
                    handleOpenModal('subListItems')
                    setModalListItems(itemsZohoSenitron?.filter(it => parseInt(it.stockOnHand, 10) - parseInt(it.quantity, 10) < 0 && it.syncedWithSenitron && !it.ignoreErrors))
                    setModalTitle(`SKUs with excess Items`)
                    setModalButtonColor('warning.main')
                    setHasIgnoredErrors(true)
                    setValueIgnoreErrors(true)
                    setIsIgnore(true)
                  }}
                />
              </Grid>

              {percentage && (
                <Grid xs={12} md={6} lg={4}>

                  <Card>
                    <CardHeader title="SKU Tracked totals" />
                    <Stack direction="column" sx={{ p: 0, textAlign: 'center' }} alignItems="center">
                      {percentage > 0 ? (
                        <>
                          <MatchGauge percentage={percentage} />
                          <Box sx={{ mt: 0, p: 0 }}>
                            <TableContainer>
                              <Table size='small'>
                                <TableBody>
                                  <TableRow>
                                    <TableCell>On Hand:</TableCell>
                                    <TableCell><b>{totalZohoQty || 0}</b></TableCell>
                                    <TableCell>RFID Count:</TableCell>
                                    <TableCell><b>{totalSenitronQty || 0}</b></TableCell>
                                  </TableRow>
                                  <TableRow>
                                    <TableCell sx={{ fontSize: '11px' }}>Correct:</TableCell>
                                    <TableCell sx={{ fontSize: '11px' }}>
                                      <Label color='success' sx={{ fontSize: '10px' }}>
                                        <b>{totalZohoQty - totalErrors || 0}</b>
                                      </Label>
                                    </TableCell>
                                    <TableCell sx={{ fontSize: '11px' }}>Mismatchs:</TableCell>
                                    <TableCell sx={{ fontSize: '11px' }}>
                                      <Label color='error' sx={{ fontSize: '10px' }}>
                                        <b>{totalErrors || 0}</b>
                                      </Label>
                                    </TableCell>
                                  </TableRow>
                                </TableBody>
                              </Table>
                            </TableContainer>
                          </Box>
                        </>
                      ) : (
                        <TableContainer sx={{ maxHeight: 350 }}>
                          <Table size='medium' stickyHeader>
                            <TableBody>
                              <TableNoData notFound={percentage <= 0} />
                            </TableBody>
                          </Table>
                        </TableContainer>
                      )}
                    </Stack>
                  </Card>
                </Grid>
              )}

              {series && (
                <Grid xs={12} md={6} lg={4}>

                  <AnalyticsCurrentVisits title="SKUs and RFID count match"
                    subheader="Number of items by percentage range"
                    element="items"
                    chart={{
                      series: seriesPieChart || [{ label: 'Items', value: 0 }],
                    }}
                    openModal={openModal}
                    setOpenModal={setOpenModal}
                    handleOpenModal={handleOpenModal}
                    modalTitle={modalTitle}
                    headersCSV={headersCSV}
                    setModalTitle={setModalTitle}
                    modalDataFiltered={modalListItems}
                    setModalDataFiltered={setModalListItems}
                    modalButtonColor={modalButtonColor}
                    setModalButtonColor={setModalButtonColor}
                    zohoItems={itemsZohoSenitron}
                    senitronItems={itemsSenitronZoho}
                    handleViewRow={handleViewRow}
                    handleFilterName={handleFilterName}
                    filters={filters}
                    table={table}
                    userLogged={userLogged}
                    hasIgnoredErrors={hasIgnoredErrors}
                    setHasIgnoredErrors={setHasIgnoredErrors}
                    ignoreErrorsSelected={ignoreErrorsSelected}
                    setIgnoreErrorsSelected={setIgnoreErrorsSelected}
                    handleCheckboxChange={handleCheckboxChange}
                    handleSelectAllIgnoreErrors={handleSelectAllIgnoreErrors}
                    isIgnore={isIgnore}
                    setIsIgnore={setIsIgnore}
                  />
                </Grid>
              )}

              {timelineItems && (
                <Grid xs={12} md={6} lg={4}>
                  <AnalyticsOrderTimeline
                    title="Items timeline"
                    list={itemsTimelineData || timelineItems}
                    isMobile={isMobile}
                    onViewDetails={handleViewRow}
                  />
                </Grid>
              )}

              <Grid xs={12} md={12} lg={12}>
                <ItemListShortView updating={updating} setUpdating={setUpdating} setTitleLinearProgress={setTitleLinearProgress} />
              </Grid>


            </Grid>
          </DashboardContent >

          <ModalSublistItems
            openModal={openModal}
            setOpenModal={setOpenModal}
            modalDataFiltered={modalDataFiltered}
            modalTitle={modalTitle}
            headersCSV={headersCSV}
            modalButtonColor={modalButtonColor}
            filters={filters}
            handleFilterName={handleFilterName}
            handleViewRow={handleViewRow}
            table={table}
            userLogged={userLogged}
            hasIgnoredErrors={hasIgnoredErrors}
            ignoreErrorsSelected={ignoreErrorsSelected}
            setIgnoreErrorsSelected={setIgnoreErrorsSelected}
            handleCheckboxChange={handleCheckboxChange}
            handleSelectAllIgnoreErrors={handleSelectAllIgnoreErrors}
            valueIgnoreErrors={valueIgnoreErrors}
            handleUpdateIgnoreErrors={handleUpdateIgnoreErrors}
            isIgnore={isIgnore}
            setIsIgnore={setIsIgnore}
          />

          <ModalListItemsSerials
            openModal={openModal}
            setOpenModal={setOpenModal}
            handleOpenModal={handleOpenModal}
            filters={filters}
            handleFilterName={handleFilterName}
            itemsAssetsLogsInfo={itemsAssetsLogsInfo}
            table={table}
          />



        </>
      )}
    </>
  );
}

function applyFilter({ inputData, comparator, filters }) {

  const { name } = filters;

  const stabilizedThis = inputData?.map((el, index) => [el, index]);

  stabilizedThis?.sort((a, b) => {
    const order = comparator(a[0], b[0]);
    if (order !== 0) return order;
    return a[1] - b[1];
  });

  inputData = stabilizedThis?.map((el) => el[0]);

  if (name) {
    inputData = inputData?.filter(
      (item) => item.name.trim().toLowerCase().indexOf(name.trim().toLowerCase()) !== -1 ||
        item.sku.trim().toLowerCase().indexOf(name.trim().toLowerCase()) !== -1 ||
        item.itemId.trim().toLowerCase().indexOf(name.trim().toLowerCase()) !== -1
    );
  }

  return inputData;
}


function processingNumbers(arrayNumbers) {
  const ranges = [
    { name: '100%', min: 100, max: Infinity, data: [0] },
    { name: '90% - 100 %', min: 90, max: 100, data: [0] },
    { name: '80% - 90%', min: 80, max: 90, data: [0] },
    { name: '70% - 80%', min: 70, max: 80, data: [0] },
    { name: '60% - 70%', min: 60, max: 70, data: [0] },
    { name: '50% - 60%', min: 50, max: 60, data: [0] },
    { name: '-50%', min: -Infinity, max: 50, data: [0] },
  ];

  arrayNumbers.forEach((number) => {
    const rangeFound = ranges.find(
      (range) => number >= range.min && number < range.max
    );
    if (rangeFound) {
      rangeFound.data[0] += 1;
    }
  });

  return ranges.map(({ name, data }) => ({ name, data }));
};

function processingNumbersPieChart(arrayNumbers) {
  const ranges = [
    { label: '100%', min: 100, max: Infinity, value: 0 },
    { label: '90% - 100 %', min: 90, max: 100, value: 0 },
    { label: '80% - 90%', min: 80, max: 90, value: 0 },
    { label: '70% - 80%', min: 70, max: 80, value: 0 },
    { label: '60% - 70%', min: 60, max: 70, value: 0 },
    { label: '50% - 60%', min: 50, max: 60, value: 0 },
    { label: '-50%', min: -Infinity, max: 50, value: 0 },
  ];

  arrayNumbers.forEach((number) => {
    const rangeFound = ranges.find(
      (range) => number >= range.min && number < range.max
    );
    if (rangeFound) {
      rangeFound.value += 1;
    }
  });

  const list = ranges.map(({ label, value }) => ({ label, value }));

  return list;
};

function linearRegresionCalculation(serie) {
  const n = serie.length;
  if (n < 2) return 0;
  let sumX = 0;
  let sumY = 0;
  let sumXY = 0;
  let sumX2 = 0;
  for (let i = 0; i < n; i += 1) {
    const x = i;
    const y = serie[i];
    sumX += x;
    sumY += y;
    sumXY += x * y;
    sumX2 += x * x;
  }
  const pendient = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const intercept = (sumY - pendient * sumX) / n;

  const firstValue = pendient * 0 + intercept;
  const lastValue = pendient * (n - 1) + intercept;
  const percentChange = ((lastValue - firstValue) / firstValue);
  return percentChange;
}

