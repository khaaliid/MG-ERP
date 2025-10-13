const Categories = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Categories</h1>
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
            Add Category
          </button>
        </div>
        
        <div className="text-center py-12">
          <span className="text-6xl">🏷️</span>
          <h3 className="text-lg font-medium text-gray-900 mt-4">No categories yet</h3>
          <p className="text-gray-600 mt-2">Organize your products by creating categories</p>
        </div>
      </div>
    </div>
  )
}

export default Categories