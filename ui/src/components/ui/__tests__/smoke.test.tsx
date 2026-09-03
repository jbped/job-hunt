import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button } from "../button";
import { Card, CardContent, CardHeader, CardTitle } from "../card";
import { Badge } from "../badge";
import { Input } from "../input";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "../dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../tabs";
import { Empty, EmptyDescription, EmptyTitle } from "../empty";

/** These components are authored against React 19; this app is on React 18.
 *  The suite exists to catch that divergence, not to test shadcn. */
describe("shadcn components under React 18", () => {
  it("renders plain compositions", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Globex</CardTitle>
        </CardHeader>
        <CardContent>
          <Badge>Applied</Badge>
          <Input aria-label="Notes" defaultValue="hello" />
          <Button>Draft the resume</Button>
        </CardContent>
      </Card>,
    );
    expect(screen.getByText("Globex")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Draft the resume" })).toBeInTheDocument();
    expect(screen.getByLabelText("Notes")).toHaveValue("hello");
  });

  it("renders an empty state", () => {
    render(
      <Empty>
        <EmptyTitle>No applications yet</EmptyTitle>
        <EmptyDescription>Capture a posting to start.</EmptyDescription>
      </Empty>,
    );
    expect(screen.getByText("No applications yet")).toBeInTheDocument();
  });

  it("switches tabs", async () => {
    const user = userEvent.setup();
    render(
      <Tabs defaultValue="posting">
        <TabsList>
          <TabsTrigger value="posting">Posting</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
        </TabsList>
        <TabsContent value="posting">the captured posting</TabsContent>
        <TabsContent value="analysis">the fit assessment</TabsContent>
      </Tabs>,
    );
    expect(screen.getByText("the captured posting")).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: "Analysis" }));
    expect(screen.getByText("the fit assessment")).toBeInTheDocument();
  });

  it("opens a radix portal overlay", async () => {
    const user = userEvent.setup();
    render(
      <Dialog>
        <DialogTrigger asChild>
          <Button>Open</Button>
        </DialogTrigger>
        <DialogContent>
          <DialogTitle>Mark as applied</DialogTitle>
        </DialogContent>
      </Dialog>,
    );
    await user.click(screen.getByRole("button", { name: "Open" }));
    expect(await screen.findByText("Mark as applied")).toBeInTheDocument();
  });

  it("renders a select with a controlled value", () => {
    render(
      <Select defaultValue="remote">
        <SelectTrigger aria-label="Work model">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="remote">Remote</SelectItem>
          <SelectItem value="hybrid">Hybrid</SelectItem>
        </SelectContent>
      </Select>,
    );
    expect(screen.getByLabelText("Work model")).toHaveTextContent("Remote");
  });
});
