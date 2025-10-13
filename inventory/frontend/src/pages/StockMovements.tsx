const StockMovements = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Stock Movements</h1>
        </div>
        
        <div className="text-center py-12">
          <span className="text-6xl">📈</span>
          <h3 className="text-lg font-medium text-gray-900 mt-4">No stock movements yet</h3>
          <p className="text-gray-600 mt-2">Track all inventory changes and movements</p>
        </div>
      </div>
    </div>
  )
}

export default StockMovements