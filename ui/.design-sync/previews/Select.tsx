import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "job-hunt-ui";

export const WorkModel = () => (
  <Select open defaultValue="remote">
    <SelectTrigger style={{ width: 220 }}>
      <SelectValue />
    </SelectTrigger>
    <SelectContent position="popper" sideOffset={4}>
      <SelectItem value="remote">Remote</SelectItem>
      <SelectItem value="hybrid">Hybrid</SelectItem>
      <SelectItem value="onsite">On site</SelectItem>
    </SelectContent>
  </Select>
);

export const Closed = () => (
  <Select defaultValue="referral">
    <SelectTrigger style={{ width: 220 }}>
      <SelectValue />
    </SelectTrigger>
    <SelectContent position="popper" sideOffset={4}>
      <SelectItem value="referral">Referral</SelectItem>
      <SelectItem value="board">Job board</SelectItem>
    </SelectContent>
  </Select>
);
