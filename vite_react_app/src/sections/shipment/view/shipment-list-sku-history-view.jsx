import dayjs from 'dayjs';
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter';
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore';

import { useMemo, useState, useEffect, useContext, useCallback } from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Table from '@mui/material/Table';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import TableBody from '@mui/material/TableBody';
import IconButton from '@mui/material/IconButton';
import TableContainer from '@mui/material/TableContainer';
import { Typography, LinearProgress } from '@mui/material';

import { paths } from 'src/routes/paths';
import { useRouter } from 'src/routes/hooks';

import { useBoolean } from 'src/hooks/use-boolean';
import { useSetState } from 'src/hooks/use-set-state';
import { useWebsocket } from 'src/hooks/use-websocket';

import { fIsAfter } from 'src/utils/format-time';

import { CONFIG } from 'src/config-global';
import { usePackagesQuery } from 'src/_mock/_package';
import { DashboardContent } from 'src/layouts/dashboard';
import { useShipmentsQuery, SHIPMENTS_STATUS_OPTIONS } from 'src/_mock/_shipment';

import { toast } from 'src/components/snackbar';
import { Iconify } from 'src/components/iconify';
import { Scrollbar } from 'src/components/scrollbar';
import { ConfirmDialog } from 'src/components/custom-dialog';
import { CustomBreadcrumbs } from 'src/components/custom-breadcrumbs';
import { TableCustomPaginationZohoStyleRow } from 'src/components/table/table-pagination-custom-zoho-style-row';
import {
  useTable,
  rowInPage,
  TableNoData,
  getComparator,
  TableHeadCustom,
  TableSelectedAction,
} from 'src/components/table';

import { LoadingContext } from 'src/auth/context/loading-context';

import { ShipmentTableRowListSkuHistory } from '../shipment-table-row-list-sku-history';
import { ShipmentTableToolbarListSkuHistory } from '../shipment-table-toolbar-list-sku-history';
import { ShipmentTableFiltersResultListSkuHistory } from '../shipment-table-filters-result-list-sku-history';

const STATUS_OPTIONS = [{ value: 'all', label: 'All' }, ...SHIPMENTS_STATUS_OPTIONS];

dayjs.extend(isSameOrAfter);
dayjs.extend(isSameOrBefore);

export function ShipmentListSkuHistoryView() {
  const start = String(dayjs().format('YYYY-MM-DD'));
  const end = String(dayjs().format('YYYY-MM-DD'));

  const filters = useSetState({
    sku: '',
    startDate: dayjs(start),
    endDate: dayjs(end),
    ignoreMull: false,
  });

  const parseLineItems = useCallback((lineItems) => {
    if (typeof lineItems === 'string') {
      try {
        return JSON.parse(lineItems).filter((item) => item.sku);
      } catch {
        return [];
      }
    }
    return (lineItems || []).filter((item) => item.sku);
  }, []);

  const parsePackages = useCallback((packages, date = null) => {
    if (typeof packages === 'string') {
      try {
        return JSON.parse(packages)
          .filter((pkg) => pkg.package_id)
          .map((pkg) => ({ ...pkg, date }));
      } catch {
        return [];
      }
    }
    return (packages || []).filter((pkg) => pkg.package_id).map((pkg) => ({ ...pkg, date }));
  }, []);

  const isWithinRange = useCallback((d, startDate, endDate) => {
    const dd = dayjs(d);
    const s = startDate ? dayjs(startDate) : null;
    const e = endDate ? dayjs(endDate) : null;
    const afterS = s ? dd.isSameOrAfter(s, 'day') : true;
    const beforeE = e ? dd.isSameOrBefore(e, 'day') : true;
    return afterS && beforeE;
  }, []);

  const { isMobile } = useContext(LoadingContext);
  const [updating, setUpdating] = useState(false);
  const [titleLinearProgress, setTitleLinearProgress] = useState('Loading data...');
  const table = useTable({ defaultOrderBy: 'itemTotalQty', defaultDense: true, defaultOrder: 'desc' });
  const router = useRouter();
  const confirm = useBoolean();

  const { data: shipments, refetch: refetchShipments } = useShipmentsQuery(
    String(filters.state.startDate.format('YYYY-MM-DD')),
    String(filters.state.endDate.format('YYYY-MM-DD'))
  );

  useEffect(() => {
    const page = localStorage.getItem('orderPage');
    if (page) {
      table.setPage(parseInt(page, 10));
    }
    const rowsPerPage = localStorage.getItem('orderRowsPerPage');
    if (rowsPerPage) {
      table.setRowsPerPage(parseInt(rowsPerPage, 10));
    }
  }, [table]);

  const allShipments = useMemo(() => shipments || [], [shipments]);

  const allPackages = useMemo(() => {
    if (!allShipments?.length) return null;
    return allShipments.map((shipment) => parsePackages(shipment.packages, shipment.date));
  }, [allShipments, parsePackages]);

  const packageIds = useMemo(
    () => allPackages?.flatMap((pkgs) => pkgs.map((pkg) => pkg.package_id)) || null,
    [allPackages]
  );

  const { data: linePackages, refetch: refetchLinePackages } = usePackagesQuery(
    null,
    null,
    packageIds
  );

  useEffect(() => {
    if (!updating) return;
    if (shipments && (packageIds === null || linePackages)) {
      setUpdating(false);
    }
  }, [updating, shipments, linePackages, packageIds]);

  const dataItems = useMemo(() => {
    if (!linePackages?.length) return [];
    return linePackages.map((pkg) => ({
      packageId: pkg.packageId,
      packageNumber: pkg.packageNumber,
      shipmentId: pkg.shipmentId,
      shipmentNumber: pkg.shipmentNumber,
      totalQuantity: pkg.totalQuantity,
      date: pkg.date,
      items: parseLineItems(pkg.lineItems) || [],
    }));
  }, [linePackages, parseLineItems]);

  const mergeItems = useMemo(() => {
    if (!dataItems?.length) return [];
    return dataItems.flatMap((itemList) =>
      itemList.items.map((item) => ({
        itemId: item.item_id,
        sku: item.sku,
        name: item.name,
        quantity: item.quantity,
        shipmentId: itemList.shipmentId,
        shipmentNumber: itemList.shipmentNumber,
        packageId: itemList.packageId,
        packageNumber: itemList.packageNumber,
        date: itemList.date,
      }))
    );
  }, [dataItems]);

  const finalGroupedArray = useMemo(() => {
    if (!mergeItems?.length) return [];
    const s = filters.state.startDate;
    const e = filters.state.endDate;
    const acc = mergeItems
      .filter((it) => isWithinRange(it.date, s, e))
      .reduce((m, it) => {
        if (!m[it.itemId]) {
          m[it.itemId] = {
            itemId: it.itemId,
            name: it.name,
            sku: it.sku,
            itemTotalQty: 0,
            packages: {},
          };
        }
        m[it.itemId].itemTotalQty += it.quantity;
        if (!m[it.itemId].packages[it.packageId]) {
          m[it.itemId].packages[it.packageId] = {
            packageId: it.packageId,
            packageNumber: it.packageNumber,
            shipmentId: it.shipmentId,
            shipmentNumber: it.shipmentNumber,
            quantity: 0,
            date: it.date,
          };
        }
        m[it.itemId].packages[it.packageId].quantity += it.quantity;
        return m;
      }, {});
    return Object.values(acc).map((g) => ({
      itemId: g.itemId,
      name: g.name,
      sku: g.sku,
      itemTotalQty: g.itemTotalQty,
      linePackages: Object.values(g.packages).map(p => ({
        packageId: p.packageId,
        packageNumber: p.packageNumber,
        shipmentId: p.shipmentId,
        shipmentNumber: p.shipmentNumber,
        quantity: p.quantity,
        date: p.date,
      })),
    }));
  }, [mergeItems, filters.state.startDate, filters.state.endDate, isWithinRange]);


  const dateError = fIsAfter(filters.state.startDate, filters.state.endDate);

  const dataFiltered = useMemo(
    () =>
      applyFilter({
        inputData: finalGroupedArray,
        comparator: getComparator(table.order, table.orderBy),
        filters: filters.state,
        dateError,
      }),
    [finalGroupedArray, table.order, table.orderBy, filters.state, dateError]
  );

  const dataInPage = rowInPage(dataFiltered, table.page, table.rowsPerPage);

  const canReset = !!filters.state.shipmentNumber || !!filters.state.endDate;
  const notFound = (!dataFiltered?.length && canReset) || !dataFiltered?.length;

  const handleDeleteRow = useCallback(
    (id) => {
      toast.success('Delete success!');
      table.onUpdatePageDeleteRow(dataInPage?.length);
    },
    [dataInPage?.length, table]
  );

  const handleDeleteRows = useCallback(() => {
    toast.success('Delete success!');
    table.onUpdatePageDeleteRows({
      totalRowsInPage: dataInPage?.length,
      totalRowsFiltered: dataFiltered?.length,
    });
  }, [dataFiltered?.length, dataInPage?.length, table]);

  const handleViewRow = useCallback(
    (id) => {
      localStorage.setItem('routeByShipmentBySku', id);
      router.push(paths.dashboard.item.details(id));
    },
    [router]
  );

  const baseWsUrl = `${CONFIG.websocketProtocol}://${CONFIG.apiHost}:${CONFIG.apiPort}/${CONFIG.apiDomain}/ws`;

  const onMessagePackages = useCallback(
    (m) => {
      if (['created', 'updated', 'deleted'].includes(m.type)) refetchLinePackages?.();
    },
    [refetchLinePackages]
  );
  useWebsocket(`${baseWsUrl}/packages/`, onMessagePackages);

  const onMessageShipments = useCallback(
    (m) => {
      if (['created', 'updated', 'deleted'].includes(m.type)) refetchShipments?.();
    },
    [refetchShipments]
  );
  useWebsocket(`${baseWsUrl}/shipment_orders/`, onMessageShipments);

  if (updating) {
    return (
      <DashboardContent>
        <Box
          sx={{
            width: '350px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '80vh',
            margin: 'auto',
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
      </DashboardContent>
    );
  }

  const TABLE_HEAD = [
    { id: 'sku', label: 'SKU', width: isMobile ? 50 : 200 },
    { id: 'name', label: 'Item', width: 50 },
    { id: 'itemTotalQty', label: 'Total Qty Shipped', width: isMobile ? 50 : 140 },
    { id: '', width: isMobile ? 30 : 68 },
  ];
  const TABLE_HEAD_MOBILE = [{ id: 'info', label: 'History SKU Shipments' }];

  return (
    <>
      <DashboardContent>
        <CustomBreadcrumbs
          heading="SKU's Shipment History"
          links={[
            { name: 'Dashboard', href: paths.dashboard.general.analytics },
            { name: 'Shipment', href: paths.dashboard.shipment.listBySku },
            { name: 'History' },
          ]}
          sx={{ mb: { xs: 3, md: 5 } }}
        />

        <Card>
          <ShipmentTableToolbarListSkuHistory
            filters={filters}
            onResetPage={table.onResetPage}
            dataFiltered={dataFiltered}
            dateError={dateError}
            setUpdating={setUpdating}
            setTitleLinearProgress={setTitleLinearProgress}
          />

          {canReset && (
            <ShipmentTableFiltersResultListSkuHistory
              filters={filters}
              totalResults={dataFiltered?.length}
              onResetPage={table.onResetPage}
              sx={{ p: 2.5, pt: 0 }}
            />
          )}

          <Box sx={{ position: 'relative' }}>
            <TableSelectedAction
              dense={table.dense}
              numSelected={table.selected.length}
              rowCount={dataFiltered?.length}
              onSelectAllRows={(checked) =>
                table.onSelectAllRows(
                  checked,
                  dataFiltered?.map((row) => row.itemId)
                )
              }
              action={
                <Tooltip title="Delete">
                  <IconButton color="primary" onClick={confirm.onTrue}>
                    <Iconify icon="solar:trash-bin-trash-bold" />
                  </IconButton>
                </Tooltip>
              }
            />

            <Scrollbar sx={{ minHeight: 444 }}>
              <TableContainer sx={{ maxHeight: 440 }}>
                <Table size={table.dense ? 'small' : 'medium'} sx={{ minWidth: !isMobile ? 960 : 380 }} stickyHeader>
                  <TableHeadCustom
                    order={table.order}
                    orderBy={table.orderBy}
                    headLabel={!isMobile ? TABLE_HEAD : TABLE_HEAD_MOBILE}
                    rowCount={dataFiltered?.length}
                    numSelected={table.selected.length}
                    onSort={table.onSort}
                    onSelectAllRows={(checked) =>
                      table.onSelectAllRows(
                        checked,
                        dataFiltered?.map((row) => row.itemId)
                      )
                    }
                  />

                  <TableBody>
                    {dataFiltered
                      ?.slice(table.page * table.rowsPerPage, table.page * table.rowsPerPage + table.rowsPerPage)
                      .map((row, index) => (
                        <ShipmentTableRowListSkuHistory
                          key={`${row.itemId}-${index}`}
                          row={row}
                          selected={table.selected.includes(row.itemId)}
                          onSelectRow={() => table.onSelectRow(row.itemId)}
                          onDeleteRow={() => handleDeleteRow(row.itemId)}
                          onViewRow={() => handleViewRow(row.itemId)}
                        />
                      ))}

                    {dataFiltered?.length > 0 && (
                      <TableCustomPaginationZohoStyleRow
                        columnsLength={isMobile ? TABLE_HEAD_MOBILE.length : TABLE_HEAD.length}
                        data={dataFiltered}
                        page={table.page}
                        rowsPerPage={table.rowsPerPage}
                        handleChangePage={(event, newPage) => {
                          localStorage.setItem('itemPage', newPage);
                          table.onChangePage(event, newPage);
                        }}
                        handleChangeRowsPerPage={(event) => {
                          localStorage.setItem('itemRowsPerPage', event.target.value);
                          table.onChangeRowsPerPage(event);
                        }}
                        dense={table.dense}
                        onChangeDense={table.onChangeDense}
                      />
                    )}

                    <TableNoData notFound={notFound} />
                  </TableBody>
                </Table>
              </TableContainer>
            </Scrollbar>
          </Box>
        </Card>
      </DashboardContent>

      <ConfirmDialog
        open={confirm.value}
        onClose={confirm.onFalse}
        title="Delete"
        content={
          <>
            Are you sure want to delete <strong> {table.selected.length} </strong> shipments?
          </>
        }
        action={
          <Button
            variant="contained"
            color="error"
            onClick={() => {
              handleDeleteRows();
              confirm.onFalse();
            }}
          >
            Delete
          </Button>
        }
      />
    </>
  );
}

function applyFilter({ inputData, comparator, filters, dateError }) {
  const { sku, ignoreMull } = filters;
  const stabilizedThis = inputData?.map((el, index) => [el, index]);
  stabilizedThis?.sort((a, b) => {
    const order = comparator(a[0], b[0]);
    if (order !== 0) return order;
    return a[1] - b[1];
  });
  let out = stabilizedThis?.map((el) => el[0]);
  if (sku) {
    const q = sku.toLowerCase();
    out = out?.filter(
      (ship) =>
        ship.sku.toLowerCase().includes(q) ||
        ship.name.toLowerCase().includes(q) ||
        ship.linePackages.some((pkg) => pkg.packageNumber.toLowerCase().includes(q)) ||
        ship.linePackages.some((pkg) => pkg.shipmentNumber.toLowerCase().includes(q))
    );
  }
  if (ignoreMull){
    out = out?.filter(
      (ship) =>
        ship.sku.toLowerCase().includes('mull-') === false
    );
  }
  return out;
}
