import { useState, useCallback, useEffect, useContext, useMemo } from 'react';

import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import Tabs from '@mui/material/Tabs';
import Card from '@mui/material/Card';
import Table from '@mui/material/Table';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import TableBody from '@mui/material/TableBody';
import TableContainer from '@mui/material/TableContainer';
import IconButton from '@mui/material/IconButton';

import { LinearProgress, Typography } from '@mui/material';

import { paths } from 'src/routes/paths';
import { useRouter } from 'src/routes/hooks';

import { useBoolean } from 'src/hooks/use-boolean';
import { useSetState } from 'src/hooks/use-set-state';

import { fIsAfter, fIsBetween } from 'src/utils/format-time';

import { varAlpha } from 'src/theme/styles';
import { DashboardContent } from 'src/layouts/dashboard';
import { SHIPMENTS_STATUS_OPTIONS, useShipmentsQuery } from 'src/_mock/_shipment';
import { usePackagesQuery } from 'src/_mock/_package';
import { CONFIG } from 'src/config-global';


import { Label } from 'src/components/label';
import { toast } from 'src/components/snackbar';
import { Iconify } from 'src/components/iconify';
import { Scrollbar } from 'src/components/scrollbar';
import { ConfirmDialog } from 'src/components/custom-dialog';
import { CustomBreadcrumbs } from 'src/components/custom-breadcrumbs';

import { LoadingContext } from 'src/auth/context/loading-context';

import {
  useTable,
  emptyRows,
  rowInPage,
  TableNoData,
  getComparator,
  TableEmptyRows,
  TableHeadCustom,
  TableSelectedAction,
  TablePaginationCustom,
} from 'src/components/table';

import { ShipmentTableRow } from '../shipment-table-row';
import { ShipmentTableToolbar } from '../shipment-table-toolbar';
import { ShipmentTableFiltersResult } from '../shipment-table-filters-result';


// ----------------------------------------------------------------------

const STATUS_OPTIONS = [{ value: 'all', label: 'All' }, ...SHIPMENTS_STATUS_OPTIONS];


// ----------------------------------------------------------------------

export function ShipmentListBySkuView() {

  const filters = useSetState({
    shipmentNumber: '',
    status: 'all',
    startDate: null,
    endDate: null,
  });

  const dateError = fIsAfter(null, filters.state.endDate);

  const parseLineItems = (lineItems) => {
    if (typeof lineItems === 'string') {
      try {
        return JSON.parse(lineItems).filter(item => item.sku);
      } catch (err) {
        console.error('Error al parsear lineItems:', err);
        return [];
      }
    } else {
      return (lineItems || []).filter(item => item.sku);
    }
  }

  const parsePackages = (packages) => {
    if (typeof packages === 'string') {
      try {
        return JSON.parse(packages).filter(pkg => pkg.package_id);
      } catch (err) {
        console.error('Error al parsear packages:', err);
        return [];
      }
    } else {
      return (packages || []).filter(pkg => pkg.package_id);
    }
  }

  const { isMobile } = useContext(LoadingContext);

  const [updating, setUpdating] = useState(false);

  const [titleLinearProgress, setTitleLinearProgress] = useState('Loading data...');

  const TABLE_HEAD = [
    { id: 'sku', label: 'SKU', width: isMobile ? 50 : 140 },
    { id: 'date', label: 'Date', width: isMobile ? 50 : 110 },
    { id: 'total_quantity', label: 'Total Qty Shipped', width: isMobile ? 50 : 140 },
    { id: '', width: isMobile ? 30 : 68 },
  ];


  const table = useTable({ defaultOrderBy: 'shipmentNumber', defaultDense: true });

  const router = useRouter();

  const confirm = useBoolean();

  const { data: shipments } = useShipmentsQuery(null, null);

  const [tableData, setTableData] = useState([]);


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


  const allShipments = useMemo(() => shipments || null, [shipments]);

  const allPackages = useMemo(() => {
    if (allShipments) {
      const packages = [];
      allShipments.forEach(shipment => {
        const parsedPackage = parsePackages(shipment.packages);
        packages.push(parsedPackage);
      });
      return packages;
    }
    return null;
  }, [allShipments]);

  // console.log('allPackages:', allPackages);


  // console.log('allShipments:', allPackages?.flatMap(pkgs => pkgs.map(pkg => pkg.package_id)) || []);

  const { data: linePackages } = usePackagesQuery(null, null, allPackages?.flatMap(pkgs => pkgs.map(pkg => pkg.package_id)));

  const allLinePackages = useMemo(() => linePackages || null, [linePackages]);

  const dataItems = useMemo(() => {
    if (linePackages) {
      const items = linePackages?.map(pkg => ({
        packageId: pkg.packageId,
        packageNumber: pkg.packageNumber,
        shipmentId: pkg.shipmentId,
        shipmentNumber: pkg.shipmentNumber,
        totalQuantity: pkg.totalQuantity,
        date: filters.state.date,
        items: parseLineItems(pkg.lineItems) || [],
      }));
      return items;
    }
    return [];
  }, [linePackages, filters.state.date]);


  // console.log('dataItems:', dataItems);


  const mergeItems = useMemo(() => {
    if (allShipments && allPackages && allLinePackages && dataItems) {
      const merged = dataItems?.flatMap(itemList => itemList.items.map(item => ({
        itemId: item.item_id,
        sku: item.sku,
        name: item.name,
        quantity: item.quantity,
        shipmentId: itemList.shipmentId,
        shipmentNumber: itemList.shipmentNumber,
        packageId: itemList.packageId,
        packageNumber: itemList.packageNumber,
        date: itemList.date,
      })));
      return merged;
    }
    return [];
  }, [allShipments, allPackages, allLinePackages, dataItems]);


  const groupedItems = mergeItems.reduce((acc, currentItem) => {
    const { itemId, name, sku, packageId, quantity, shipmentId, shipmentNumber, packageNumber, date } = currentItem;
    if (!acc[itemId]) {
      acc[itemId] = {
        itemId,
        name,
        sku,
        date,
        itemTotalQty: 0,
        linePackages: []
      };
    }
    acc[itemId].itemTotalQty += quantity;
    acc[itemId].linePackages.push({
      packageId,
      packageNumber,
      quantity,
      shipmentId,
      shipmentNumber
    });
    return acc;
  }, {});

  const finalGroupedArray = Object.values(groupedItems);

  console.log('finalGroupedArray:', finalGroupedArray);

  const dataFiltered = applyFilter({
    inputData: tableData,
    comparator: getComparator(table.order, table.orderBy),
    filters: filters.state,
    dateError,
  });

  const dataInPage = rowInPage(dataFiltered, table.page, table.rowsPerPage);

  const canReset =
    !!filters.state.shipmentNumber ||
    filters.state.status !== 'all' ||
    !!filters.state.endDate;

  const notFound = (!dataFiltered.length && canReset) || !dataFiltered.length;




  // useEffect(() => {
  //   if (data && data.length > 0) {
  //     setTableData(data);
  //   } else {
  //     console.error("No data returned from useShipmentsQuery");
  //     setTableData([]);
  //   }
  // }, [data]);



  const handleDeleteRow = useCallback(
    (id) => {
      const deleteRow = tableData.filter((row) => row.shipmentId !== id);

      toast.success('Delete success!');

      setTableData(deleteRow);

      table.onUpdatePageDeleteRow(dataInPage.length);
    },
    [dataInPage.length, table, tableData]
  );

  const handleDeleteRows = useCallback(() => {
    const deleteRows = tableData.filter((row) => !table.selected.includes(row.shipmentId));

    toast.success('Delete success!');

    setTableData(deleteRows);

    table.onUpdatePageDeleteRows({
      totalRowsInPage: dataInPage.length,
      totalRowsFiltered: dataFiltered.length,
    });
  }, [dataFiltered.length, dataInPage.length, table, tableData]);

  const handleViewRow = useCallback(
    (id) => {
      router.push(paths.dashboard.order.details(id));
    },
    [router]
  );

  const handleFilterStatus = useCallback(
    (event, newValue) => {
      table.onResetPage();
      filters.setState({ status: newValue });
    },
    [filters, table]
  );

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
      </DashboardContent>
    );
  }

  return (
    <>
      <DashboardContent>
        <CustomBreadcrumbs
          heading="List"
          links={[
            { name: 'Dashboard', href: paths.dashboard.general.analytics },
            { name: 'Shipment', href: paths.dashboard.shipment.root },
            { name: 'List' },
          ]}
          sx={{ mb: { xs: 3, md: 5 } }}
        />

        <Card>
          <Tabs
            value={filters.state.status}
            onChange={handleFilterStatus}
            sx={{
              px: 2.5,
              boxShadow: (theme) =>
                `inset 0 -2px 0 0 ${varAlpha(theme.vars.palette.grey['500Channel'], 0.08)}`,
            }}
          >
            {STATUS_OPTIONS.map((tab) => (
              <Tab
                key={tab.value}
                iconPosition="end"
                value={tab.value}
                label={tab.label}
                icon={
                  <Label
                    variant={
                      ((tab.value === 'all' || tab.value === filters.state.status) && 'filled') ||
                      'soft'
                    }
                    color={
                      (tab.value === 'delivered' && 'success') ||
                      (tab.value === 'partially_shipped' && 'warning') ||
                      'default'
                    }
                  >
                    {['delivered', 'partially_shipped', 'draft'].includes(tab.value)
                      ? tableData.filter((it) => it.status === tab.value).length
                      : tableData.length}
                  </Label>
                }
              />
            ))}
          </Tabs>

          <ShipmentTableToolbar
            filters={filters}
            onResetPage={table.onResetPage}
            dateError={dateError}
            setUpdating={setUpdating}
            setTitleLinearProgress={setTitleLinearProgress}
          />

          {canReset && (
            <ShipmentTableFiltersResult
              filters={filters}
              totalResults={dataFiltered.length}
              onResetPage={table.onResetPage}
              sx={{ p: 2.5, pt: 0 }}
            />
          )}

          <Box sx={{ position: 'relative' }}>
            <TableSelectedAction
              dense={table.dense}
              numSelected={table.selected.length}
              rowCount={dataFiltered.length}
              onSelectAllRows={(checked) =>
                table.onSelectAllRows(
                  checked,
                  dataFiltered.map((row) => row.shipmentId)
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
                <Table size={table.dense ? 'small' : 'medium'} sx={{ minWidth: 960 }} stickyHeader>
                  <TableHeadCustom
                    order={table.order}
                    orderBy={table.orderBy}
                    headLabel={TABLE_HEAD}
                    rowCount={dataFiltered.length}
                    numSelected={table.selected.length}
                    onSort={table.onSort}
                    onSelectAllRows={(checked) =>
                      table.onSelectAllRows(
                        checked,
                        dataFiltered.map((row) => row.shipmentId)
                      )
                    }
                  />

                  <TableBody>
                    {dataFiltered
                      .slice(
                        table.page * table.rowsPerPage,
                        table.page * table.rowsPerPage + table.rowsPerPage
                      )
                      .map((row, index) => (
                        <ShipmentTableRow
                          key={`${row.shipmentId}-${index}`}
                          row={row}
                          selected={table.selected.includes(row.shipmentId)}
                          onSelectRow={() => table.onSelectRow(row.shipmentId)}
                          onDeleteRow={() => handleDeleteRow(row.shipmentId)}
                          onViewRow={() => handleViewRow(row.shipmentId)}
                        />
                      ))}

                    <TableEmptyRows
                      height={table.dense ? 56 : 56 + 20}
                      emptyRows={emptyRows(table.page, table.rowsPerPage, dataFiltered.length)}
                    />

                    <TableNoData notFound={notFound} />
                  </TableBody>
                </Table>
              </TableContainer>
            </Scrollbar>
          </Box>

          <TablePaginationCustom
            page={table.page}
            dense={table.dense}
            count={dataFiltered.length}
            rowsPerPage={table.rowsPerPage}
            onPageChange={(event, newPage) => {
              localStorage.setItem('orderPage', newPage);
              table.onChangePage(event, newPage);
            }}
            onChangeDense={table.onChangeDense}
            onRowsPerPageChange={(event) => {
              localStorage.setItem('orderRowsPerPage', event.target.value);
              table.onChangeRowsPerPage(event);
            }}
          />
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
  const { status, shipmentNumber, startDate, endDate } = filters;

  const stabilizedThis = inputData.map((el, index) => [el, index]);

  stabilizedThis.sort((a, b) => {
    const order = comparator(a[0], b[0]);
    if (order !== 0) return order;
    return a[1] - b[1];
  });

  inputData = stabilizedThis.map((el) => el[0]);

  if (shipmentNumber) {
    inputData = inputData.filter(
      (ship) => (
        ship.shipmentNumber.toLowerCase().indexOf(shipmentNumber.toLowerCase()) !== -1
      )
    );
  }

  if (status !== 'all') {
    inputData = inputData.filter((ship) => ship.status === status);
  }

  if (!dateError) {
    if (startDate && endDate) {
      inputData = inputData.filter((ship) => fIsBetween(ship.date, startDate, endDate));
    }
    else if (endDate) {
      const oneDayBefore = new Date(endDate) - 1;
      inputData = inputData.filter((ship) => fIsBetween(ship.date, oneDayBefore, endDate));
    }
  }

  return inputData;
}
