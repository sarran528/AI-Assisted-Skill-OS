import { SidebarLayout } from "../components/layout/SidebarLayout";

// Example of how to use the new layout for any view
export function ExampleView() {
  return (
    <SidebarLayout>
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">Page Title</h1>
        <p className="text-muted-foreground">
          This is how any view should be structured with the new sidebar layout.
          The sidebar is fixed on the left, and this content takes the remaining width.
        </p>
        
        {/* Your page content goes here */}
        <div className="mt-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Example content cards */}
            <div className="p-4 border rounded">
              <h3 className="font-semibold mb-2">Content Card 1</h3>
              <p className="text-sm text-muted-foreground">Some content here</p>
            </div>
            <div className="p-4 border rounded">
              <h3 className="font-semibold mb-2">Content Card 2</h3>
              <p className="text-sm text-muted-foreground">More content here</p>
            </div>
            <div className="p-4 border rounded">
              <h3 className="font-semibold mb-2">Content Card 3</h3>
              <p className="text-sm text-muted-foreground">Even more content</p>
            </div>
          </div>
        </div>
      </div>
    </SidebarLayout>
  );
}
