import { jsPDF as JsPDF } from 'jspdf';
import 'jspdf-autotable';
import logoBase64 from '../../public/files/color_white_background/icon_with_text/PNG.png';
import { fDateTime } from './format-time';

export const generatePrintablePDF = ({ data, title }) => {

    const currentYear = new Date().getFullYear();

    const doc = new JsPDF('p', 'pt', 'a4');

    const margin = 40;
    const logoWidth = 120;
    const logoHeight = 40;

    doc.addImage(logoBase64, 'PNG', margin, margin, logoWidth, logoHeight);

    doc.setFontSize(11);
    doc.text(` ${title}`, margin + logoWidth + 10, margin + 30);

    const date = new Date().toLocaleDateString();
    doc.setFontSize(10);
    doc.text(`Date: ${date}`, doc.internal.pageSize.getWidth() - margin - 100, margin + 30);

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
    doc.text(`Date: ${date}`, doc.internal.pageSize.getWidth() - margin - 100, margin + 30);

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

// ----------------------------------------------------------------------

export const generateItemShipmentPrintablePDF = ({ data }) => {
    const doc = new JsPDF('p', 'pt', 'a4'); 

    const margin = 40;
    const logoWidth = 120;
    const logoHeight = 40;
    let currentY = margin;
    
    if (logoBase64) {
        doc.addImage(logoBase64, 'PNG', margin, currentY, logoWidth, logoHeight);
    }

    const title = 'Items in Shipments';
    
    doc.setFontSize(16);
    // doc.setFont('helvetica', 'bold');
    doc.text(title, margin + logoWidth + 10, currentY + 25);
    
    const date = new Date().toLocaleDateString();
    doc.setFontSize(10);
    // doc.setFont('helvetica', 'normal');
    doc.text(`Date: ${date}`, doc.internal.pageSize.getWidth() - margin - 100, currentY + 25);

    currentY += logoHeight + 30; 

    data?.forEach((item, index) => {
        const estimatedHeight = 100; 
        if (currentY + estimatedHeight > doc.internal.pageSize.getHeight() - margin) {
            addFooter(doc, margin);
            doc.addPage();
            currentY = margin;
            
            if (logoBase64) {
                doc.addImage(logoBase64, 'PNG', margin, currentY, logoWidth, logoHeight);
            }

            doc.setFontSize(16);
            doc.setFont('helvetica', 'bold');
            doc.text(title, margin + logoWidth + 10, currentY + 25);

            doc.setFontSize(10);
            // doc.setFont('helvetica', 'normal');
            doc.text(`Date: ${date}`, doc.internal.pageSize.getWidth() - margin - 100, currentY + 25);

            currentY += logoHeight + 30;
        }
        
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text(`Item ID: ${item.itemId}`, margin, currentY);
        currentY += 15;
        doc.setFont('helvetica', 'normal');
        doc.text(`SKU: ${item.sku}`, margin, currentY);
        currentY += 15;
        doc.text(`Date: ${item.date}`, margin, currentY);
        currentY += 15;
        doc.text(`Total Quantity: ${item.itemTotalQty}`, margin, currentY);
        currentY += 15;
        
        const packagesData = item.linePackages.map(pkg => ({
            packageId: pkg.packageId,
            packageNumber: pkg.packageNumber,
            quantity: pkg.quantity,
            shipmentId: pkg.shipmentId,
            shipmentNumber: pkg.shipmentNumber,
        }));

        const packageColumns = [
            { header: 'Package ID', dataKey: 'packageId' },
            { header: '# Package', dataKey: 'packageNumber' },
            { header: 'Quantity', dataKey: 'quantity' },
            { header: 'Shipment ID', dataKey: 'shipmentId' },
            { header: '# Shipment', dataKey: 'shipmentNumber' },
        ];
        
        doc.autoTable({
            head: [packageColumns.map(col => col.header)],
            body: packagesData.map(pkg => packageColumns.map(col => pkg[col.dataKey])),
            startY: currentY,
            margin: { left: margin + 20, right: margin },
            styles: { fontSize: 10 },
            headStyles: { fillColor: [22, 160, 133], halign: 'center' },
            theme: 'striped',
            showHead: 'firstPage',
            didDrawPage: (d) => {
                addFooter(doc, margin);
            },
        });

        currentY = doc.previousAutoTable.finalY + 20; 

        doc.setDrawColor(200);
        doc.line(margin, currentY, doc.internal.pageSize.getWidth() - margin, currentY);
        currentY += 10;
    });
    
    addFooter(doc, margin);
    
    const pdfBlob = doc.output('blob');

    const blobUrl = URL.createObjectURL(pdfBlob);

    window.open(blobUrl, '_blank');

    setTimeout(() => {
        URL.revokeObjectURL(blobUrl);
    }, 1000);
};

const addFooter = (doc, margin) => {
    const currentYear = new Date().getFullYear();
    const pageCount = doc.internal.getNumberOfPages();
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    doc.text(`Page ${doc.internal.getCurrentPageInfo().pageNumber} de ${pageCount}`, pageWidth / 2, pageHeight - margin / 2, { align: 'center' });
    doc.text(`© ${currentYear} NWS. Warehouse Management System. All rights reserved.`, pageWidth / 2, pageHeight - margin / 2 + 10, { align: 'center' });
};
