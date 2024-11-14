import { jsPDF as JsPDF } from 'jspdf';
import 'jspdf-autotable';
import logoBase64 from '../../public/files/color_white_background/icon_with_text/PNG.png';
import { fDateTime } from './format-time';

export const generatePrintablePDF = ({ data, title }) => {
    const doc = new JsPDF('p', 'pt', 'a4');

    const margin = 40;
    const logoWidth = 120;
    const logoHeight = 40;

    doc.addImage(logoBase64, 'PNG', margin, margin, logoWidth, logoHeight);

    doc.setFontSize(11);
    doc.text(` ${title}`, margin + logoWidth + 10, margin + 30);

    const date = new Date().toLocaleDateString();
    doc.setFontSize(10);
    doc.text(`Fecha: ${date}`, doc.internal.pageSize.getWidth() - margin - 100, margin + 30);

    const columns = [
        { dataKey: 'index', header: '#' },
        { dataKey: 'sku', header: 'SKU' },
        { dataKey: 'stockOnHand', header: 'On Hand' },
        { dataKey: 'quantity', header: 'RFID Count' },
        { dataKey: 'difference', header: 'Difference' },
    ];

    const rows = data.map((item, index) => ({
        index: index + 1,
        sku: item.sku,
        stockOnHand: item.stockOnHand,
        quantity: item.quantity,
        difference: item.difference,
    }));

    doc.autoTable({
        columns,
        body: rows,
        startY: margin + logoHeight + 40,
        margin: { horizontal: margin },
        styles: { fontSize: 12 },
        headStyles: { fillColor: [22, 160, 133] },
        theme: 'striped',
        didDrawPage: (items) => {
            const pageCount = doc.internal.getNumberOfPages();
            doc.setFontSize(10);
            const pageWidth = doc.internal.pageSize.getWidth();
            const pageHeight = doc.internal.pageSize.getHeight();
            doc.text(`Page ${doc.internal.getCurrentPageInfo().pageNumber} of ${pageCount}`, pageWidth / 2, pageHeight - margin / 2, { align: 'center' });
            doc.text('© 2024 NWS. Warehouse Management System. All rights reserved.', pageWidth / 2, pageHeight - margin / 2 + 10, { align: 'center' });
        },
    });

    const pdfBlob = doc.output('blob');

    const blobUrl = URL.createObjectURL(pdfBlob);

    window.open(blobUrl, '_blank');

    setTimeout(() => {
        URL.revokeObjectURL(blobUrl);
    }, 1000);
};


// ----------------------------------------------------------------------


export const generateItemPrintablePDF = ({ item, senitronItem }) => {

    const currentYear = new Date().getFullYear();

    const doc = new JsPDF('p', 'pt', 'a4');

    const margin = 40;
    const logoWidth = 120;
    const logoHeight = 40;

    doc.addImage(logoBase64, 'PNG', margin, margin, logoWidth, logoHeight);

    doc.setFontSize(11);
    doc.text(` Details: ${item.sku}`, margin + logoWidth + 10, margin + 30);

    const date = new Date().toLocaleDateString();
    doc.setFontSize(10);
    doc.text(`Fecha: ${date}`, doc.internal.pageSize.getWidth() - margin - 100, margin + 30);

    const generalInfoColumns = [
        { dataKey: 'field', header: 'Campo' },
        { dataKey: 'value', header: 'Valor' },
    ];

    const generalInfoRows = [
        { field: 'Name', value: item.name },
        { field: 'SKU', value: item.sku },
        { field: 'On Hand', value: item.stockOnHand },
        { field: 'RFID Count', value: senitronItem.count },
        { field: 'Difference', value: senitronItem.count - item.stockOnHand },
        { field: 'Description', value: item.description },
        { field: 'Price', value: item.rate },
        { field: 'Type of Product', value: item.productType },
        { field: 'Group', value: item.groupName },
        { field: 'Status', value: item.status },
        { field: 'Origin', value: item.source },
        { field: 'Type of Item', value: item.itemType },
        { field: 'Linked with ZohoCRM', value: item.isLinkedWithZohocrm ? 'YES' : 'NO' },
    ];

    doc.autoTable({
        columns: generalInfoColumns,
        body: generalInfoRows,
        startY: margin + logoHeight + 40,
        margin: { horizontal: margin },
        styles: { fontSize: 12 },
        headStyles: { fillColor: [22, 160, 133] },
        theme: 'striped',
    });

    const assetsStartY = doc.lastAutoTable.finalY + 20;

    const assetsColumns = [
        { dataKey: 'id', header: 'ID' },
        { dataKey: 'serialNumber', header: 'Serial Number' },
        { dataKey: 'firstSeen', header: 'First Seen' },
        { dataKey: 'lastSeen', header: 'Last Seen' },
        { dataKey: 'lastZone', header: 'Last Zone' },
        { dataKey: 'status', header: 'Status' },
    ];

    const assetsRows = senitronItem.assets.map(asset => ({
        id: asset.id,
        serialNumber: asset.serialNumber,
        firstSeen: fDateTime(asset.firstSeen),
        lastSeen: fDateTime(asset.lastSeen),
        lastZone: asset.lastZone,
        status: asset.status.name,
    }));

    doc.setFontSize(14);
    doc.text('Assets:', margin + 25, assetsStartY - 2, { align: 'center' });

    doc.autoTable({
        columns: assetsColumns,
        body: assetsRows,
        startY: assetsStartY,
        margin: { horizontal: margin },
        styles: { fontSize: 12 },
        headStyles: { fillColor: [22, 160, 133] },
        theme: 'striped',
        didDrawPage: () => {
            const pageCount = doc.internal.getNumberOfPages();
            doc.setFontSize(10);
            const pageWidth = doc.internal.pageSize.getWidth();
            const pageHeight = doc.internal.pageSize.getHeight();
            doc.text(`Page ${doc.internal.getCurrentPageInfo().pageNumber} of ${pageCount}`, pageWidth / 2, pageHeight - margin / 2, { align: 'center' });
            doc.text(`© ${currentYear} NWS. Warehouse Management System. All rights reserved.`, pageWidth / 2, pageHeight - margin / 2 + 10, { align: 'center' });
        },
    });

    const pdfBlob = doc.output('blob');

    const blobUrl = URL.createObjectURL(pdfBlob);

    window.open(blobUrl, '_blank');

    setTimeout(() => {
        URL.revokeObjectURL(blobUrl);
    }, 1000);
};
