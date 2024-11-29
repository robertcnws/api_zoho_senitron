import { useState, useCallback, useEffect, useContext, useMemo } from 'react';
import axios from 'axios';
import Box from '@mui/material/Box';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Card from '@mui/material/Card';
import Table from '@mui/material/Table';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import TableBody from '@mui/material/TableBody';
import TableContainer from '@mui/material/TableContainer';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import { LinearProgress, TableCell, TableRow } from '@mui/material';

import { paths } from 'src/routes/paths';
import { useRouter } from 'src/routes/hooks';

import { useBoolean } from 'src/hooks/use-boolean';
import { useSetState } from 'src/hooks/use-set-state';


import { varAlpha } from 'src/theme/styles';
import { DashboardContent } from 'src/layouts/dashboard';
import { ITEM_STATUS_SHORT_OPTIONS, ITEM_SYNC_OPTIONS, useItemsQuery, useSenitronItemsQuery } from 'src/_mock/_items';
import { CONFIG } from 'src/config-global';

import { Label } from 'src/components/label';
import { toast } from 'src/components/snackbar';
import { Iconify } from 'src/components/iconify';
import { Scrollbar } from 'src/components/scrollbar';
import { ConfirmDialog } from 'src/components/custom-dialog';

import { LoadingContext } from 'src/auth/context/loading-context';
import { fDate } from 'src/utils/format-time';

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

import { ItemTableRow } from '../item-table-row';
import { ItemTableToolbar } from '../item-table-toolbar';
import { ItemTableFiltersResult } from '../item-table-filters-result';



// ----------------------------------------------------------------------

const STATUS_OPTIONS = [
    { value: 'all', label: 'All SKUs' },
    { value: 'lost', label: 'Losts Shipped SKUs' },
    { value: 'not_matched', label: 'Shipped SKUs NOT reconciled' },
    { value: 'matched', label: 'Shipped SKUs matched' },

];

const headersCSV = [
    { label: 'SKU', key: 'sku' },
    { label: 'Qty Shipped', key: 'itemTotalQty' },
    { label: 'RFID Count', key: 'shipmentSerialsQuantity' },
    { label: 'Difference', key: 'differenceShipped' },
]

// ----------------------------------------------------------------------

export function ItemListShippedLogsView({ 
    listSerials, 
    listShipments, 
    itemsZohoSenitron,
    setTotalsItemsNoReconciled,
    setTotalsItemsLost,
    setTotalsItemsAll,
    updating, 
    setUpdating, 
    setTitleLinearProgress 
}) {

    const date = fDate(new Date(), 'YYYY-MM-DD');

    const { isMobile } = useContext(LoadingContext);

    const TABLE_HEAD = [
        { id: 'sku', label: 'SKU', width: isMobile ? 100 : 250 },
        { id: 'itemTotalQty', label: 'Qty Shipped', width: isMobile ? 50 : 100 },
        { id: 'shipmentSerialsQuantity', label: 'RFID Count', width: isMobile ? 50 : 100 },
        { id: 'differenceShipped', label: 'Difference', width: isMobile ? 50 : 100 },
    ];

    const table = useTable({ defaultDense: true });

    const router = useRouter();

    const confirm = useBoolean();

    const [tableData, setTableData] = useState([]);

    const filters = useSetState({ name: '', status: STATUS_OPTIONS.includes(localStorage.getItem('itemStatus')) ? localStorage.getItem('itemStatus') : 'all' });


    useEffect(() => {
        localStorage.removeItem('routeByAnalytics');
        localStorage.removeItem('routeByOrder');
        localStorage.removeItem('routeByShipment');
        localStorage.removeItem('routeByShipmentBySku');
    }, []);


    useEffect(() => {
        const page = localStorage.getItem('itemPage');
        if (page) {
            table.setPage(parseInt(page, 10));
        }
        const rowsPerPage = localStorage.getItem('itemRowsPerPage');
        if (rowsPerPage) {
            table.setRowsPerPage(parseInt(rowsPerPage, 10));
        }
    }, [table]);


    const handleShippedSerialQuantity = useCallback(
        (itemShipped) => itemShipped?.historialDifferences.reduce(
            (acc, h, index) => acc + (index !== itemShipped.historialDifferences.length - 1 ? h.differences.losts.length : 0), 0
        ), []
    );


    listShipments = useMemo(() => listShipments?.filter((item) => item.date === date), [listShipments, date]);

    // console.log('listShipments', listShipments);


    useEffect(() => {
        if (listSerials && listSerials.length > 0 && listShipments && listShipments.length > 0) {

            const rData = listShipments?.map((item) => {
                const senitronItem = listSerials?.find((sItem) => sItem?.itemId === item.itemId);
                return {
                    ...item,
                    shippedSerialsQuantity: handleShippedSerialQuantity(senitronItem) || 0,
                    differenceShipped: handleShippedSerialQuantity(senitronItem) ?
                        (item.itemTotalQty - handleShippedSerialQuantity(senitronItem)) : item.itemTotalQty,
                    receivedSerialsQuantity: senitronItem?.historialDifferences.reduce(
                        (acc, h, index) => acc + (index !== senitronItem.historialDifferences.length - 1 ? h.differences.news.length : 0), 0
                    ) || 0,
                    isReconciled: false,
                };
            });

            const rDataZohoSenitron = rData?.map((item) => {
                const senitronItem = itemsZohoSenitron?.find((sItem) => sItem?.itemId === item.itemId);
                return {
                    ...item,
                    isReconciled: parseInt(senitronItem.stockOnHand, 10) - parseInt(senitronItem.quantity, 10) === 0,
                }

            });

            setTableData(rDataZohoSenitron);
        }
    }, [listSerials, listShipments, itemsZohoSenitron, handleShippedSerialQuantity]);

    setTotalsItemsLost(useMemo(() => 
        tableData?.filter((item) => item.differenceShipped < 0 && !item.isReconciled).length, 
    [tableData]));

    setTotalsItemsNoReconciled(useMemo(() =>
        tableData?.filter((item) => item.differenceShipped > 0 && !item.isReconciled).length,
    [tableData]));

    setTotalsItemsAll(useMemo(() => tableData?.length, [tableData]));

    const dataFiltered = applyFilter({
        inputData: tableData,
        comparator: getComparator(table.order, table.orderBy),
        filters: filters.state,
    });

    const dataInPage = rowInPage(dataFiltered, table.page, table.rowsPerPage);

    const canReset =
        !!filters.state.name || filters.state.status !== 'all';

    const notFound = (!dataFiltered.length && canReset) || !dataFiltered.length;

    const handleFilterStatus = useCallback(
        (event, newValue) => {
            table.onResetPage();
            localStorage.setItem('itemStatus', newValue);
            filters.setState({ status: newValue });
        },
        [filters, table]
    );

    const handleViewRow = useCallback(
        (id) => {
            localStorage.removeItem('routeByOrder');
            localStorage.removeItem('routeByShipment');
            localStorage.setItem('routeByAnalytics', id);
            localStorage.setItem('itemStatus', filters.state.status);
            router.push(paths.dashboard.item.details(id));
        },
        [router, filters]
    );

    if (!tableData || tableData.length === 0) {
        return (
            <DashboardContent>
                <Box display="flex" alignItems="center" mb={5}>
                    <Alert severity="warning" sx={{ borderRadius: 0 }}>
                        <Typography>No items found</Typography>
                    </Alert>
                </Box>
            </DashboardContent>
        );
    }

    if (updating) {
        return (
            <DashboardContent>
                <Box
                    sx={{
                        width: '350px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        height: '80vh',
                        margin: 'auto'
                    }}
                >
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
            <Card>
                <Tabs
                    value={filters.state.status}
                    onChange={handleFilterStatus}
                    sx={{
                        bgcolor: 'whitesmoke',
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
                            sx={{
                                bgcolor: tab.value === 'lost' && tableData.filter((it) => it.differenceShipped < 0 && !it.isReconciled).length > 0 ? 'error.main' :
                                    tab.value === 'not_matched' && tableData.filter((it) => it.differenceShipped > 0 && !it.isReconciled).length > 0 ? 'warning.main' : 'transparent',
                                color: tab.value === 'lost' && tableData.filter((it) => it.differenceShipped < 0 && !it.isReconciled).length > 0 ? 'white' : 'inherit',
                                px: 1.5,
                                py: 1,
                                borderRadius: '8px',
                            }}
                            icon={
                                <Label
                                    variant={
                                        ((tab.value === 'lost' || tab.value === 'not_matched' || tab.value === filters.state.status) && 'filled') ||
                                        'soft'
                                    }
                                    color={
                                        (tab.value === 'matched' && 'success') ||
                                        (tab.value === 'not_matched' && 'warning') ||
                                        (tab.value === 'lost' && 'error') ||
                                        'default'
                                    }
                                >
                                    {tab.value === 'matched' ?
                                        tableData.filter((it) => it.differenceShipped === 0).length :
                                        tab.value === 'not_matched' ?
                                            tableData.filter((it) => it.differenceShipped > 0 && !it.isReconciled).length :
                                            tab.value === 'lost' ?
                                                tableData.filter((it) => it.differenceShipped < 0 && !it.isReconciled).length :
                                                tableData.length
                                    }
                                </Label>
                            }
                        />
                    ))}
                </Tabs>

                <ItemTableToolbar
                    filters={filters}
                    onResetPage={table.onResetPage}
                    options={{ values: STATUS_OPTIONS.map((option) => option.label) }}
                    dataFiltered={dataFiltered}
                    headersCSV={headersCSV}
                    setUpdating={setUpdating}
                    setTitleLinearProgress={setTitleLinearProgress}
                    isListAll={false}
                    title={filters.state.status === 'all' ? 'All SKUs' :
                        filters.state.status === 'lost' ? 'Losts Shipped SKUs' :
                            filters.state.status === 'matched' ? 'Shipped SKUs matched' :
                                filters.state.status === 'not_matched' ? 'Shipped SKUs NOT matched' :
                                    filters.state.status
                    }
                />

                {canReset && (
                    <ItemTableFiltersResult
                        filters={filters}
                        totalResults={dataFiltered.length}
                        onResetPage={table.onResetPage}
                        hasNotAll={false}
                        sx={{ p: 2.5, pt: 0 }}
                    />
                )}

                <Box sx={{ position: 'relative' }}>

                    <Scrollbar>
                        <TableContainer sx={{
                            maxHeight: filters.state.status === 'all' ? 255 : 155,
                            minHeight: filters.state.status === 'all' ? 255 : 155
                        }}>
                            <Table size={table.dense ? 'small' : 'medium'} sx={{ minWidth: 960 }} stickyHeader>
                                <TableHeadCustom
                                    order={table.order}
                                    orderBy={table.orderBy}
                                    headLabel={TABLE_HEAD}
                                    rowCount={dataFiltered.length}
                                    numSelected={table.selected.length}
                                    onSort={table.onSort}
                                />

                                <TableBody>
                                    {dataFiltered
                                        .slice(
                                            table.page * table.rowsPerPage,
                                            table.page * table.rowsPerPage + table.rowsPerPage
                                        )
                                        .map((row) => (
                                            <TableRow key={row.itemId}>
                                                <TableCell>{row.sku}</TableCell>
                                                <TableCell>{row.itemTotalQty}</TableCell>
                                                <TableCell>
                                                    {!row.isReconciled ? row.shippedSerialsQuantity : row.itemTotalQty}
                                                </TableCell>
                                                <TableCell>
                                                    <Label
                                                        sx={{ cursor: 'pointer' }}
                                                        variant="soft"
                                                        color={
                                                            (row.differenceShipped === 0 ? 'success' : 
                                                                row.differenceShipped > 0 && !row.isReconciled ? 'warning' : 
                                                                row.differenceShipped < 0 && !row.isReconciled ? 'error' : 'info')
                                                        }
                                                    >
                                                        {!row.isReconciled ? row.differenceShipped : 0}
                                                    </Label>
                                                </TableCell>
                                            </TableRow>
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
                        localStorage.setItem('itemPage', newPage);
                        table.onChangePage(event, newPage);
                    }}
                    onChangeDense={table.onChangeDense}
                    onRowsPerPageChange={(event) => {
                        localStorage.setItem('itemRowsPerPage', event.target.value);
                        table.onChangeRowsPerPage(event);
                    }}
                />
            </Card>
        </>
    );
}

function applyFilter({ inputData, comparator, filters }) {
    const { name, status } = filters;

    const stabilizedThis = inputData.map((el, index) => [el, index]);

    stabilizedThis.sort((a, b) => {
        const order = comparator(a[0], b[0]);
        if (order !== 0) return order;
        return a[1] - b[1];
    });

    inputData = stabilizedThis.map((el) => el[0]);

    if (name) {
        inputData = inputData.filter(
            (item) => item.name.toLowerCase().indexOf(name.toLowerCase()) !== -1 ||
                item.sku.toLowerCase().indexOf(name.toLowerCase()) !== -1 ||
                item.itemId.toString().indexOf(name.toLowerCase()) !== -1
        );
    }
    if (status === 'lost') {
        inputData = inputData.filter((item) => item.differenceShipped < 0 && !item.isReconciled);
    } else if (status === 'matched') {
        inputData = inputData.filter((item) => item.differenceShipped === 0);
    } else if (status === 'not_matched') {
        inputData = inputData.filter((item) => item.differenceShipped > 0 && !item.isReconciled);
    }
    return inputData;
}
