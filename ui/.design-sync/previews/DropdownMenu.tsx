import {
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "job-hunt-ui";

export const ApplicationActions = () => (
  <DropdownMenu open>
    <DropdownMenuTrigger asChild>
      <Button variant="outline">Actions</Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="start" className="w-56">
      <DropdownMenuLabel>Globex</DropdownMenuLabel>
      <DropdownMenuSeparator />
      <DropdownMenuItem>Open the posting</DropdownMenuItem>
      <DropdownMenuItem>Draft the resume</DropdownMenuItem>
      <DropdownMenuItem>Log an interview</DropdownMenuItem>
      <DropdownMenuSeparator />
      <DropdownMenuItem>Archive</DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
);
