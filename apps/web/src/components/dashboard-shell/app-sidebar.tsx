import { Button } from "@citetrack/ui/button";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@citetrack/ui/sidebar";
import { Skeleton } from "@citetrack/ui/skeleton";
import { UserButton, useUser } from "@clerk/react";
import { Link, useLocation } from "@tanstack/react-router";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  BarChart3,
  FileSearch,
  LayoutDashboard,
  Lightbulb,
  MessageSquareQuote,
  Quote,
  Search as SearchIcon,
  Settings,
  Swords,
  Tag,
} from "lucide-react";
import { WorkspaceSwitcher } from "#/features/workspaces/workspace-switcher";

interface NavItem {
  testId: string;
  label: string;
  to: string;
  icon: LucideIcon;
}

const personalNavItems: NavItem[] = [
  { testId: "dashboard", label: "My Tracking", to: "/dashboard", icon: LayoutDashboard },
];

const dataNavItems: NavItem[] = [
  { testId: "scans", label: "Scans", to: "/dashboard/scans", icon: Activity },
  { testId: "prompts", label: "Prompts", to: "/dashboard/prompts", icon: MessageSquareQuote },
  { testId: "citations", label: "AI Responses", to: "/dashboard/citations", icon: Quote },
];

const insightsNavItems: NavItem[] = [
  { testId: "actions", label: "Action Plan", to: "/dashboard/actions", icon: Lightbulb },
  { testId: "content-analysis", label: "Content Analysis", to: "/dashboard/content-analysis", icon: FileSearch },
  { testId: "pixel", label: "Pixel", to: "/dashboard/pixel", icon: BarChart3 },
];

const configureNavItems: NavItem[] = [
  { testId: "brands", label: "Brands", to: "/dashboard/brands", icon: Tag },
  { testId: "competitors", label: "Competitors", to: "/dashboard/competitors", icon: Swords },
  { testId: "settings", label: "Settings", to: "/dashboard/settings", icon: Settings },
];

function NavGroup({
  label,
  items,
  currentPathname,
}: {
  label?: string;
  items: NavItem[];
  currentPathname: string;
}) {
  return (
    <SidebarGroup>
      {label ? <SidebarGroupLabel>{label}</SidebarGroupLabel> : null}
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => {
            const Icon = item.icon;
            const isActive = currentPathname === item.to;
            return (
              <SidebarMenuItem key={item.to}>
                <SidebarMenuButton asChild isActive={isActive} data-testid={`sidebar-link-${item.testId}`}>
                  <Link to={item.to}>
                    <Icon className="size-4" />
                    <span>{item.label}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            );
          })}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}

function UserFooter() {
  const { user, isLoaded } = useUser();

  if (!isLoaded) {
    return (
      <div className="border-t pt-2 flex items-center gap-2.5 px-2 py-1.5">
        <Skeleton className="size-7 rounded-full" />
        <div className="flex-1 space-y-1">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-3 w-32" />
        </div>
      </div>
    );
  }

  return (
    <div className="border-t pt-2 flex items-center gap-2.5 px-2 py-1.5">
      <UserButton appearance={{ elements: { avatarBox: "size-7" } }} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium leading-tight">
          {user?.fullName ?? user?.firstName ?? "Signed in"}
        </p>
        <p className="truncate text-xs text-muted-foreground leading-tight">
          {user?.primaryEmailAddress?.emailAddress}
        </p>
      </div>
    </div>
  );
}

export function AppSidebar() {
  const location = useLocation();

  return (
    <Sidebar>
      <SidebarHeader>
        <WorkspaceSwitcher />
        <Button
          variant="ghost"
          className="w-full justify-start gap-2 h-9 text-sm text-muted-foreground"
        >
          <SearchIcon className="size-4" />
          Search...
          <kbd className="ml-auto text-[10px] font-mono bg-muted px-1.5 py-0.5 rounded">⌘K</kbd>
        </Button>
      </SidebarHeader>
      <SidebarContent>
        <NavGroup items={personalNavItems} currentPathname={location.pathname} />
        <NavGroup label="Data" items={dataNavItems} currentPathname={location.pathname} />
        <NavGroup label="Insights" items={insightsNavItems} currentPathname={location.pathname} />
        <NavGroup label="Configure" items={configureNavItems} currentPathname={location.pathname} />
      </SidebarContent>
      <SidebarFooter>
        <UserFooter />
      </SidebarFooter>
    </Sidebar>
  );
}
