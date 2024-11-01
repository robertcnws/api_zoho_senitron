import React, { useState, useEffect, useCallback } from 'react';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Unstable_Grid2';
import { Box, Card, CardHeader, Stack, Table, TableBody, TableCell, TableContainer, TableRow } from '@mui/material';
import { paths } from 'src/routes/paths';
import { useRouter } from 'src/routes/hooks';
import { useSetState } from 'src/hooks/use-set-state';
import MatchGauge from 'src/components/chart/gauge-chart';
import { TableNoData } from 'src/components/table';


import { CONFIG } from 'src/config-global';
import { useItemsQuery, useSenitronItemsQuery } from 'src/_mock/_items';
import { DashboardContent } from 'src/layouts/dashboard';
import {
  _analyticTasks,
  _analyticPosts,
  _analyticTraffic,
  _analyticOrderTimeline,
} from 'src/_mock';

import { useTimelineItemsQuery } from 'src/_mock/_timelineItems';

import { AnalyticsNews } from '../analytics-news';
import { AnalyticsOrderTimeline } from '../analytics-order-timeline';
import { AnalyticsWebsiteVisits } from '../analytics-website-visits';
import { AnalyticsWidgetSummary } from '../analytics-widget-summary';
import { ModalSublistItems } from './modal-sublist-items';


// ----------------------------------------------------------------------

export function OverviewAnalyticsView() {

  const router = useRouter();

  const { loading, error, data: items } = useItemsQuery();
  const { data: senitronItems } = useSenitronItemsQuery();
  const { data: timelineItems } = useTimelineItemsQuery();

  const [itemsTimelineData, setItemsTimelineData] = useState(timelineItems);
  const [itemsZohoData, setItemsZohoData] = useState(null);
  const [itemsSenitronData, setItemsSenitronData] = useState(null);

  const [itemsSynced, setItemsSynced] = useState(null);
  const [itemsMismatched, setItemsMismatched] = useState(null);
  const [itemsZohoSenitron, setItemsZohoSenitron] = useState(null);
  const [itemsZohoMismatched, setItemsZohoMismatched] = useState(null);
  const [percentage, setPercentage] = useState(null);
  const [totalZohoQty, setTotalZohoQty] = useState(null);
  const [totalSenitronQty, setTotalSenitronQty] = useState(null);

  const [categories, setCategories] = useState(null);
  const [series, setSeries] = useState(null);

  const [openModal, setOpenModal] = useState(false);
  const [modalListItems, setModalListItems] = useState(null);
  const [modalTitle, setModalTitle] = useState(null);
  const [modalButtonColor, setModalButtonColor] = useState(null);

  const filters = useSetState({ name: '' });

  const modalDataFiltered = applyFilter({
    inputData: modalListItems,
    filters: filters.state,
  });

  const handleFilterName = useCallback(
    (event) => {
      filters.setState({ name: event.target.value });
    },
    [filters]
  );

  const processingNumbers = (arrayNumbers) => {
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

  const usernameLogged = JSON.parse(localStorage.getItem('userLogged'));

  useEffect(() => {
    if (items) {
      setItemsZohoData(items);
    }
  }, [items]);

  useEffect(() => {
    const socket = new WebSocket(`wss://${CONFIG.apiHost}/${CONFIG.apiDomain}/ws/inventory_items/`);
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'created' || message.type === 'updated') {
        setItemsZohoData((prevData) => {
          const existingItemIndex = prevData.findIndex(item => item.itemId === message.item.itemId);
          if (existingItemIndex !== -1) {
            const updatedData = [...prevData];
            updatedData[existingItemIndex] = message.item;
            return updatedData;
          }
          return [message.item, ...prevData];
        });
      }
    };
    return () => {
      socket.close();
    };
  }, []);

  useEffect(() => {
    const socket = new WebSocket(`wss://${CONFIG.apiHost}/${CONFIG.apiDomain}/ws/senitron_timelines/`);
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'created' || message.type === 'updated') {
        setItemsTimelineData((prevData) => {
          const existingItemIndex = prevData.findIndex(item => item.id === message.item.id);
          if (existingItemIndex !== -1) {
            const updatedData = [...prevData];
            updatedData[existingItemIndex] = message.item;
            return updatedData;
          }
          return [message.item, ...prevData];
        });
      }
    };
    return () => {
      socket.close();
    };
  }, []);


  useEffect(() => {
    if (itemsZohoData) {
      const iSynced = itemsZohoData.filter(item => item.syncedWithSenitron);
      setItemsSynced(iSynced);
      let tSenitronQty = 0;
      if (senitronItems) {
        tSenitronQty = senitronItems.reduce((acc, senitronItem) => acc + senitronItem.senitronItem.qty, 0);
        setTotalSenitronQty(tSenitronQty);
      }
      const tZohoQty = iSynced?.reduce((acc, item) => acc + item.stockOnHand, 0);
      setTotalZohoQty(tZohoQty);
      const max = Math.max(tZohoQty, tSenitronQty);
      const min = Math.min(tZohoQty, tSenitronQty);
      const match = Math.floor((min / max) * 100) || 0;
      setPercentage(match);
    }
  }, [itemsZohoData, senitronItems]);

  useEffect(() => {
    if (itemsZohoData && senitronItems) {
      const mismatchedItems = senitronItems.filter(senitronItem => {
        const item = itemsZohoData.find(it => it.itemId === senitronItem.itemNumber);
        return item && item.stockOnHand !== senitronItem.senitronItem.qty;
      });
      setItemsMismatched(mismatchedItems);
      setItemsZohoMismatched(itemsZohoData.filter(item => {
        const senitronItem = mismatchedItems.find(sItem => sItem.itemNumber === item.itemId);
        return senitronItem
      }));
    }
  }, [itemsZohoData, senitronItems]);

  useEffect(() => {
    if (itemsZohoData && senitronItems) {
      const zohoSenitronItems = itemsZohoData.filter(item => {
        const senitronItem = senitronItems.find(sItem => sItem.itemNumber === item.itemId);
        return senitronItem;
      });
      setItemsZohoSenitron(zohoSenitronItems);
    }
  }, [itemsZohoData, senitronItems]);

  useEffect(() => {
    if (itemsZohoData && senitronItems) {
      const itemsSync = itemsZohoData.filter(item => item.syncedWithSenitron);
      const sseries = itemsSync.map(item => {
        const senitronItem = senitronItems?.find(sItem => sItem.itemNumber === item.itemId);
        const zohoQty = item?.stockOnHand || 0;
        const senitronQty = senitronItem?.senitronItem.qty || 0;
        const max = Math.max(zohoQty, senitronQty);
        const min = Math.min(zohoQty, senitronQty);
        const match = Math.floor((min / max) * 100) || 0;
        return match;
      });
      const sseriesAvg = processingNumbers(sseries);
      setSeries(sseriesAvg);
      setCategories(['Items']);
    }

  }, [itemsZohoData, senitronItems]);


  const handleViewRow = useCallback(
    (id) => {
      localStorage.removeItem('routeByOrder');
      localStorage.setItem('routeByAnalytics', id);
      router.push(paths.dashboard.item.details(id));
    },
    [router]
  );


  return (
    <>
      <DashboardContent maxWidth="xl">
        <Typography variant="h4" sx={{ mb: { xs: 3, md: 5 } }}>
          Hi {usernameLogged.data.username}, Welcome back 👋
        </Typography>

        <Grid container spacing={3}>
          <Grid xs={12} sm={6} md={3}>
            <AnalyticsWidgetSummary
              sx={{ cursor: 'pointer' }}
              title="Items Synced"
              percent={2.6}
              total={itemsSynced?.length}
              icon={
                <img alt="icon" src={`${CONFIG.assetsDir}/assets/icons/glass/ic-item-synced.svg`} />
              }
              chart={{
                categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'],
                series: [22, 8, 35, 50, 82, 84, 77, 12],
              }}
              onClick={() => {
                setOpenModal(true)
                setModalListItems(itemsSynced)
                setModalTitle('Items Synced')
                setModalButtonColor('#4CAF50')
              }}
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <AnalyticsWidgetSummary
              sx={{ cursor: 'pointer' }}
              title="Items from Zoho"
              percent={-0.1}
              total={items?.length}
              color="secondary"
              icon={
                <img alt="icon" src={`${CONFIG.assetsDir}/assets/icons/glass/ic-item-zoho.svg`} />
              }
              chart={{
                categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'],
                series: [56, 47, 40, 62, 73, 30, 23, 54],
              }}
              onClick={() => {
                setOpenModal(true)
                setModalListItems(items)
                setModalTitle('Items from Zoho')
                setModalButtonColor('info.main')
              }}
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <AnalyticsWidgetSummary
              sx={{ cursor: 'pointer' }}
              title="Items from Senitron"
              percent={2.8}
              total={senitronItems?.length}
              color="warning"
              icon={
                <img alt="icon" src={`${CONFIG.assetsDir}/assets/icons/glass/ic-item-senitron.svg`} />
              }
              chart={{
                categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'],
                series: [40, 70, 50, 28, 70, 75, 7, 64],
              }}
              onClick={() => {
                setOpenModal(true)
                setModalListItems(itemsZohoSenitron)
                setModalTitle('Items from Sentitron')
                setModalButtonColor('#FF9800')
              }}
            />
          </Grid>

          <Grid xs={12} sm={6} md={3}>
            <AnalyticsWidgetSummary
              sx={{ cursor: 'pointer' }}
              title="Mismatched Synced Items"
              percent={3.6}
              total={itemsMismatched?.length}
              color="error"
              icon={
                <img alt="icon" src={`${CONFIG.assetsDir}/assets/icons/glass/ic-item-mismatch.svg`} />
              }
              chart={{
                categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'],
                series: [56, 30, 23, 54, 47, 40, 62, 73],
              }}
              onClick={() => {
                setOpenModal(true)
                setModalListItems(itemsZohoMismatched)
                setModalTitle('Mismatched Synced Items')
                setModalButtonColor('#F44336')
              }}
            />
          </Grid>

          {percentage && (

            <Grid xs={12} md={6} lg={4}>
              {/* <AnalyticsCurrentVisits
              title="Current visits"
              chart={{
                series: [
                  { label: 'America', value: 3500 },
                  { label: 'Asia', value: 2500 },
                  { label: 'Europe', value: 1500 },
                  { label: 'Africa', value: 500 },
                ],
              }}
            /> */}
              <Card>
                <CardHeader title="Total Matched Items" />
                <Stack direction="column" sx={{ p: 0, textAlign: 'center' }} alignItems="center">
                  {percentage > 0 ? (
                    <>
                      <MatchGauge percentage={percentage} />
                      <Box sx={{ mt: 0, p: 0 }}>

                        <TableContainer>
                          <Table size='small'>
                            <TableBody>
                              <TableRow>
                                <TableCell>Total Zoho Quantity:</TableCell>
                                <TableCell><b>{totalZohoQty}</b></TableCell>
                              </TableRow>
                              <TableRow>
                                <TableCell>Total Senitron Quantity:</TableCell>
                                <TableCell><b>{totalSenitronQty}</b></TableCell>
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
                          <TableNoData notFound={percentage > 0} />
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
              <AnalyticsWebsiteVisits
                title="Quantity Match"
                subheader="Number of items by percentage range"
                element="items"
                chart={{
                  categories: categories || ['Items'],
                  series: series || [{ name: 'Items', data: [0] }],
                }}
                openModal={openModal}
                setOpenModal={setOpenModal}
                modalTitle={modalTitle}
                setModalTitle={setModalTitle}
                modalDataFiltered={modalListItems}
                setModalDataFiltered={setModalListItems}
                modalButtonColor={modalButtonColor}
                setModalButtonColor={setModalButtonColor}
                zohoItems={itemsZohoData}
                senitronItems={senitronItems}
                handleViewRow={handleViewRow}
                handleFilterName={handleFilterName}
                filters={filters}
              />
            </Grid>
          )}

          {timelineItems && (
            <Grid xs={12} md={6} lg={4}>
              <AnalyticsOrderTimeline title="Items timeline" list={itemsTimelineData || timelineItems} onViewDetails={handleViewRow} />
            </Grid>
          )}

          {/* <Grid xs={12} md={6} lg={8}>
          <AnalyticsConversionRates
            title="Conversion rates"
            subheader="(+43%) than last year"
            chart={{
              categories: ['Italy', 'Japan', 'China', 'Canada', 'France'],
              series: [
                { name: '2022', data: [44, 55, 41, 64, 22] },
                { name: '2023', data: [53, 32, 33, 52, 13] },
              ],
            }}
          />
        </Grid> */}

          {/* <Grid xs={12} md={6} lg={4}>
          <AnalyticsCurrentSubject
            title="Current subject"
            chart={{
              categories: ['English', 'History', 'Physics', 'Geography', 'Chinese', 'Math'],
              series: [
                { name: 'Series 1', data: [80, 50, 30, 40, 100, 20] },
                { name: 'Series 2', data: [20, 30, 40, 80, 20, 80] },
                { name: 'Series 3', data: [44, 76, 78, 13, 43, 10] },
              ],
            }}
          />
        </Grid> */}

          <Grid xs={12} md={12} lg={12}>
            <AnalyticsNews title="News" list={_analyticPosts} />
          </Grid>



          {/* <Grid xs={12} md={6} lg={4}>
          <AnalyticsTrafficBySite title="Traffic by site" list={_analyticTraffic} />
        </Grid>

        <Grid xs={12} md={6} lg={8}>
          <AnalyticsTasks title="Tasks" list={_analyticTasks} />
        </Grid> */}
        </Grid>
      </DashboardContent>

      <ModalSublistItems
        openModal={openModal}
        setOpenModal={setOpenModal}
        modalDataFiltered={modalDataFiltered}
        modalTitle={modalTitle}
        modalButtonColor={modalButtonColor}
        filters={filters}
        handleFilterName={handleFilterName}
        handleViewRow={handleViewRow}
      />

    </>
  );
}

function applyFilter({ inputData, filters }) {

  const { name } = filters;

  if (name) {
    inputData = inputData?.filter(
      (item) => item.name.trim().toLowerCase().indexOf(name.trim().toLowerCase()) !== -1 ||
        item.sku.trim().toLowerCase().indexOf(name.trim().toLowerCase()) !== -1 ||
        item.itemId.trim().toLowerCase().indexOf(name.trim().toLowerCase()) !== -1
    );
  }

  return inputData;
}
