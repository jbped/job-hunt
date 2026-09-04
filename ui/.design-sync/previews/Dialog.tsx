import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "job-hunt-ui";

export const MarkAsApplied = () => (
  <Dialog open>
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Mark as applied</DialogTitle>
        <DialogDescription>
          Records the submission date and moves Globex to the applied stage.
        </DialogDescription>
      </DialogHeader>
      <DialogFooter>
        <Button variant="outline">Cancel</Button>
        <Button>Mark as applied</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);
