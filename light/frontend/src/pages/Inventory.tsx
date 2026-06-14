import React, { useEffect, useState } from 'react';
import { api, inventoryAPI } from '../api';
import { useTranslation } from 'react-i18next';
import '../i18n';

interface InventoryItem {
  id: number;
  name: string;
  sku: string;
  barcode?: string;
  category?: string;
  unit_price: number;
  cost_price: number;
  quantity: number;
  reorder_level: number;
}

function Inventory() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showBarcodeModal, setShowBarcodeModal] = useState(false);
  const [selectedItemForBarcode, setSelectedItemForBarcode] = useState<InventoryItem | null>(null);
  const [barcodeImageUrl, setBarcodeImageUrl] = useState<string | null>(null);
  const [barcodeImageLoading, setBarcodeImageLoading] = useState(false);
  const [barcodeImageError, setBarcodeImageError] = useState('');
  const [barcodePrintCount, setBarcodePrintCount] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    barcode: '',
    category: '',
    unit_price: '',
    cost_price: '',
    quantity: '',
    reorder_level: '10',
  });

  const { t } = useTranslation();

  useEffect(() => {
    loadItems();
  }, []);

  useEffect(() => {
    let currentBlobUrl: string | null = null;

    const loadBarcodeImage = async () => {
      if (!showBarcodeModal || !selectedItemForBarcode) {
        setBarcodeImageUrl(null);
        setBarcodeImageError('');
        setBarcodeImageLoading(false);
        return;
      }

      try {
        setBarcodeImageLoading(true);
        setBarcodeImageError('');

        const response = await api.get(`/inventory/${selectedItemForBarcode.id}/barcode`, {
          responseType: 'blob',
        });

        currentBlobUrl = URL.createObjectURL(response.data);
        setBarcodeImageUrl(currentBlobUrl);
      } catch (err: any) {
        setBarcodeImageUrl(null);
        setBarcodeImageError(err.response?.data?.detail || 'Failed to load barcode image');
      } finally {
        setBarcodeImageLoading(false);
      }
    };

    loadBarcodeImage();

    return () => {
      if (currentBlobUrl) {
        URL.revokeObjectURL(currentBlobUrl);
      }
    };
  }, [showBarcodeModal, selectedItemForBarcode]);

  const loadItems = async () => {
    try {
      setLoading(true);
      const response = await inventoryAPI.getAll({ search: searchTerm });
      setItems(response.data);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || t('Failed_to_load_inventory'));
    } finally {
      setLoading(false);
    }
  };

  const generateBarcode = (productName: string) => {
    // Generate a 12-digit barcode based on product name and timestamp
    // Format: 2 (product code) + 9 digits from name hash + 2 random digits
    if (!productName || productName.length < 2) {
      return '';
    }
    
    const nameHash = productName
      .split('')
      .reduce((acc, char) => acc + char.charCodeAt(0), 0);
    
    const timestamp = Date.now().toString().slice(-2);
    const hashStr = Math.abs(nameHash).toString().padStart(7, '0').slice(-7);
    
    // Format: 2 + 7 digits from hash + 2 timestamp + 1 will be checksum by backend
    const barcode = '2' + hashStr + timestamp;
    
    // Ensure exactly 12 digits
    return barcode.padStart(12, '0').slice(0, 12);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const itemData = {
        ...formData,
        unit_price: parseFloat(formData.unit_price),
        cost_price: parseFloat(formData.cost_price),
        quantity: parseInt(formData.quantity),
        reorder_level: parseInt(formData.reorder_level),
      };

      if (editingItem) {
        // Update existing item
        await inventoryAPI.update(editingItem.id, itemData);
      } else {
        // Create new item
        await inventoryAPI.create(itemData);
      }
      
      setShowForm(false);
      setEditingItem(null);
      setFormData({
        name: '',
        sku: '',
        barcode: '',
        category: '',
        unit_price: '',
        cost_price: '',
        quantity: '',
        reorder_level: '10',
      });
      loadItems();
    } catch (err: any) {
      alert(err.response?.data?.detail || `Failed to ${editingItem ? 'update' : 'create'} item`);
    }
  };

  const handleEdit = (item: InventoryItem) => {
    setEditingItem(item);
    setFormData({
      name: item.name,
      sku: item.sku,
      barcode: item.barcode || '',
      category: item.category || '',
      unit_price: item.unit_price.toString(),
      cost_price: item.cost_price.toString(),
      quantity: item.quantity.toString(),
      reorder_level: item.reorder_level.toString(),
    });
    setShowForm(true);
  };

  const handleCancelEdit = () => {
    setShowForm(false);
    setEditingItem(null);
    setFormData({
      name: '',
      sku: '',
      barcode: '',
      category: '',
      unit_price: '',
      cost_price: '',
      quantity: '',
      reorder_level: '10',
    });
  };

  const handleShowBarcode = (item: InventoryItem) => {
    setSelectedItemForBarcode(item);
    setBarcodePrintCount(1);
    setShowBarcodeModal(true);
  };

  const handlePrintBarcode = async () => {
    if (selectedItemForBarcode) {
      try {
        // Check if browser supports Web Serial API
        if (!('serial' in navigator)) {
          alert('⚠️ Web Serial API not supported in this browser.\n\nPlease use Chrome, Edge, or Opera browser for direct printing.\n\nAlternatively, use "Print Image" button.');
          return;
        }

        // Download ESC/POS barcode data
        const response = await api.get(`/inventory/${selectedItemForBarcode.id}/barcode/escpos`, {
          responseType: 'arraybuffer',
        });

        if (response.status === 503) {
          alert('ESC/POS library not available on server.\n\n' +
                'Thermal printing requires the python-escpos library.\n\n' +
                'You can use the "Print Image" button for regular printers.');
          return;
        }

        const data = new Uint8Array(response.data);
        
        // Request serial port access
        const port = await (navigator as any).serial.requestPort();
        await port.open({ baudRate: 9600 });
        
        // Write ESC/POS data to the printer (repeat for requested count)
        const writer = port.writable.getWriter();
        for (let i = 0; i < barcodePrintCount; i++) {
          await writer.write(data);
        }
        writer.releaseLock();
        
        // Close the port
        await port.close();
        
        alert('✅ Barcode printed successfully!');
        setShowBarcodeModal(false);
        
      } catch (error: any) {
        console.error('Error printing barcode:', error);

        if (error.response?.status === 503) {
          alert('ESC/POS library not available on server.\n\n' +
                'Thermal printing requires the python-escpos library.\n\n' +
                'You can use the "Print Image" button for regular printers.');
          return;
        }
        
        if (error.name === 'NotFoundError') {
          alert('❌ No printer selected.\n\nPlease select your thermal printer when prompted.');
        } else if (error.name === 'NetworkError') {
          alert('❌ Could not connect to printer.\n\nMake sure the printer is turned on and connected.');
        } else {
          alert('❌ Failed to print barcode.\n\n' + 
                'Error: ' + error.message + '\n\n' +
                'Try using "Print Image" button instead.');
        }
      }
    }
  };

  const handlePrintBarcodeImage = () => {
    // Fallback: Print barcode as image (for non-thermal printers)
    if (selectedItemForBarcode) {
      if (!barcodeImageUrl) {
        alert(barcodeImageError || 'Barcode image not loaded yet. Please try again.');
        return;
      }

      const printWindow = window.open('', '_blank');
      if (printWindow) {
        const barcodeItems = Array.from({ length: barcodePrintCount }, () =>
          `<div class="barcode-item">
            <h2>${selectedItemForBarcode.name}</h2>
            <div class="info">SKU: ${selectedItemForBarcode.sku}</div>
            <div class="info">Price: $${selectedItemForBarcode.unit_price.toFixed(2)}</div>
            <img src="${barcodeImageUrl}" alt="Barcode" />
          </div>`
        ).join('');
        printWindow.document.write(`
          <html>
            <head>
              <title>Print Barcode - ${selectedItemForBarcode.name}</title>
              <style>
                body {
                  margin: 0;
                  padding: 20px;
                  display: flex;
                  flex-direction: column;
                  align-items: center;
                  font-family: Arial, sans-serif;
                }
                .barcode-item {
                  display: flex;
                  flex-direction: column;
                  align-items: center;
                  margin-bottom: 20px;
                  page-break-inside: avoid;
                }
                h2 { margin: 10px 0; }
                img { margin: 10px 0; }
                .info { text-align: center; margin: 4px 0; }
                @media print {
                  button { display: none; }
                }
              </style>
            </head>
            <body>
              ${barcodeItems}
              <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; cursor: pointer;">Print</button>
            </body>
          </html>
        `);
        printWindow.document.close();
      }
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      try {
        await inventoryAPI.delete(id);
        loadItems();
      } catch (err: any) {
        alert(err.response?.data?.detail || 'Failed to delete item');
      }
    }
  };

  const getStockStatus = (quantity: number, reorderLevel: number) => {
    if (quantity === 0) return { color: '#e74c3c', text: t('Out_of_Stock') };
    if (quantity <= reorderLevel) return { color: '#f39c12', text: t('Low_Stock') };
    return { color: '#27ae60', text: t('In_Stock') };
  };

  const filteredItems = items.filter(item => 
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (item.barcode && item.barcode.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div>
      <h1>📦 {t('inventory_title')}</h1>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
          <input
            type="text"
            placeholder={t('search_placeholder')}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && loadItems()}
            style={{ width: '300px', padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
          />
          <div>
            <button 
              className="button button-primary" 
              onClick={loadItems}
              style={{ marginRight: '10px' }}
            >
              🔍 {t('search')}
            </button>
            <button className="button button-primary" onClick={() => !showForm ? setShowForm(true) : handleCancelEdit()}>
              {showForm ? t('cancel') : `+ ${t('add_item')}`}
            </button>
          </div>
        </div>

        {showForm && (
          <form onSubmit={handleSubmit} style={{ marginBottom: '30px', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '5px' }}>
            <h3 style={{ marginTop: 0, color: '#2c3e50' }}>
              {editingItem ? `${t('edit_product')}: ${editingItem.name}` : t('add_new_product')}
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              <div className="form-group">
                <label>{t('product_name')} *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => {
                    const newName = e.target.value;
                    setFormData({ 
                      ...formData, 
                      name: newName,
                      // Auto-generate barcode if it's empty and not editing
                      barcode: !editingItem && !formData.barcode && newName.length > 2 
                        ? generateBarcode(newName) 
                        : formData.barcode
                    });
                  }}
                />
              </div>
              <div className="form-group">
                <label>{t('sku')} * {editingItem && <span style={{ fontSize: '12px', color: '#7f8c8d' }}>(Cannot be changed)</span>}</label>
                <input
                  type="text"
                  required
                  value={formData.sku}
                  onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                  disabled={!!editingItem}
                  style={{ backgroundColor: editingItem ? '#e0e0e0' : 'white' }}
                />
              </div>
              <div className="form-group">
                <label>{t('barcode')} <span style={{ fontSize: '12px', color: '#7f8c8d' }}>(Auto-generated, can be edited)</span></label>
                <div style={{ display: 'flex', gap: '5px' }}>
                  <input
                    type="text"
                    value={formData.barcode}
                    onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                    placeholder={t('barcode_placeholder')}
                  />
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, barcode: generateBarcode(formData.name) })}
                    className="button"
                    style={{ padding: '8px 12px', fontSize: '12px', whiteSpace: 'nowrap' }}
                    disabled={!formData.name}
                    title={t('regenerate_barcode')}
                  >
                    🔄 {t('regenerate_barcode')}
                  </button>
                </div>
              </div>
              <div className="form-group">
                <label>{t('category')}</label>
                <input
                  type="text"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>{t('unit_price')} *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={formData.unit_price}
                  onChange={(e) => setFormData({ ...formData, unit_price: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>{t('cost_price')} *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={formData.cost_price}
                  onChange={(e) => setFormData({ ...formData, cost_price: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>{t('quantity')} *</label>
                <input
                  type="number"
                  required
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>{t('reorder_level')} *</label>
                <input
                  type="number"
                  required
                  value={formData.reorder_level}
                  onChange={(e) => setFormData({ ...formData, reorder_level: e.target.value })}
                />
              </div>
            </div>
            <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
              <button type="submit" className="button button-success">
                {editingItem ? `💾 ${t('update_item')}` : `✓ ${t('create_item')}`}
              </button>
              {editingItem && (
                <button type="button" className="button" onClick={handleCancelEdit} style={{ backgroundColor: '#95a5a6', color: 'white' }}>
                  {t('cancel')}
                </button>
              )}
            </div>
          </form>
        )}

        {loading ? (
          <p>{t('loading_inventory')}</p>
        ) : error ? (
          <p style={{ color: 'red' }}>{error}</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>{t('name')}</th>
                  <th>{t('sku')}</th>
                  <th>{t('barcode')}</th>
                  <th>{t('category')}</th>
                  <th>{t('unit_price')}</th>
                  <th>{t('cost_price')}</th>
                  <th>{t('quantity')}</th>
                  <th>{t('status')}</th>
                  <th>{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => {
                  const status = getStockStatus(item.quantity, item.reorder_level);
                  return (
                    <tr key={item.id}>
                      <td>{item.name}</td>
                      <td>{item.sku}</td>
                      <td>{item.barcode || '-'}</td>
                      <td>{item.category || '-'}</td>
                      <td>${item.unit_price.toFixed(2)}</td>
                      <td>${item.cost_price.toFixed(2)}</td>
                      <td>{item.quantity}</td>
                      <td>
                        <span style={{ 
                          color: status.color, 
                          fontWeight: 'bold',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          backgroundColor: status.color + '20'
                        }}>
                          {status.text}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '5px' }}>
                          <button
                            className="button button-primary"
                            onClick={() => handleEdit(item)}
                            style={{ padding: '5px 10px', fontSize: '12px' }}
                            title={t('edit_item')}
                          >
                            ✏️ {t('edit')}
                          </button>
                          <button
                            className="button"
                            onClick={() => handleShowBarcode(item)}
                            style={{ padding: '5px 10px', fontSize: '12px', backgroundColor: '#3498db', color: 'white' }}
                            title={t('print_barcode')}
                          >
                            🏷️ {t('barcode')}
                          </button>
                          <button
                            className="button button-danger"
                            onClick={() => handleDelete(item.id)}
                            style={{ padding: '5px 10px', fontSize: '12px' }}
                            title={t('delete_item')}
                          >
                            🗑️
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {!loading && !error && filteredItems.length === 0 && (
          <p style={{ textAlign: 'center', color: '#7f8c8d', marginTop: '20px' }}>
            {searchTerm ? 'No items found matching your search.' : 'No inventory items yet. Add your first item!'}
          </p>
        )}
      </div>

      {/* Barcode Modal */}
      {showBarcodeModal && selectedItemForBarcode && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000,
          }}
          onClick={() => setShowBarcodeModal(false)}
        >
          <div
            style={{
              backgroundColor: 'white',
              padding: '30px',
              borderRadius: '10px',
              maxWidth: '600px',
              width: '90%',
              textAlign: 'center',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ marginTop: 0, color: '#2c3e50' }}>{selectedItemForBarcode.name}</h2>
            <p style={{ color: '#7f8c8d' }}>
              SKU: {selectedItemForBarcode.sku} | Price: ${selectedItemForBarcode.unit_price.toFixed(2)}
            </p>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              margin: '12px 0',
              padding: '12px 20px',
              backgroundColor: '#eaf4fb',
              border: '1px solid #aed6f1',
              borderRadius: '8px',
            }}>
              <label htmlFor="barcode-print-count" style={{ fontWeight: 700, fontSize: '15px', color: '#1a5276' }}>
                🖨️ How many to print:
              </label>
              <input
                id="barcode-print-count"
                type="number"
                min={1}
                max={500}
                value={barcodePrintCount}
                onChange={(e) => setBarcodePrintCount(Math.max(1, parseInt(e.target.value) || 1))}
                style={{
                  width: '75px',
                  padding: '8px 10px',
                  fontSize: '16px',
                  fontWeight: 700,
                  border: '2px solid #2980b9',
                  borderRadius: '6px',
                  textAlign: 'center',
                  color: '#1a5276',
                  backgroundColor: 'white',
                }}
              />
            </div>
            <div style={{ margin: '20px 0', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '5px' }}>
              {barcodeImageLoading ? (
                <p>{t('loading')}...</p>
              ) : barcodeImageError ? (
                <p style={{ color: 'red' }}>{barcodeImageError}</p>
              ) : barcodeImageUrl ? (
                <img
                  src={barcodeImageUrl}
                  alt="Barcode"
                  style={{ maxWidth: '100%', height: 'auto' }}
                />
              ) : (
                <p style={{ color: '#7f8c8d' }}>No barcode image available.</p>
              )}
            </div>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
              <button
                className="button button-success"
                onClick={handlePrintBarcode}
                style={{ padding: '12px 24px', fontSize: '14px' }}
                title="Download ESC/POS file for thermal printer"
              >
                🖨️ Print to Thermal Printer
              </button>
              <button
                className="button"
                onClick={handlePrintBarcodeImage}
                style={{ padding: '12px 24px', fontSize: '14px', backgroundColor: '#3498db', color: 'white' }}
                title="Print as image (regular printer)"
              >
                🖼️ Print Image
              </button>
              <button
                className="button"
                onClick={() => setShowBarcodeModal(false)}
                style={{ padding: '12px 24px', fontSize: '14px', backgroundColor: '#95a5a6', color: 'white' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Inventory;
