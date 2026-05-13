import { createContext, useCallback, useContext, useRef, useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../components/ui/alert-dialog";

const ConfirmContext = createContext(null);

const DEFAULTS = {
  title: "Are you sure?",
  description: "This action cannot be undone.",
  confirmLabel: "Confirm",
  cancelLabel: "Cancel",
  destructive: false,
};

export function ConfirmProvider({ children }) {
  const [open, setOpen] = useState(false);
  const [opts, setOpts] = useState(DEFAULTS);
  const resolverRef = useRef(null);

  const confirm = useCallback((options = {}) => {
    setOpts({ ...DEFAULTS, ...options });
    setOpen(true);
    return new Promise((resolve) => {
      resolverRef.current = resolve;
    });
  }, []);

  const handle = (value) => {
    setOpen(false);
    resolverRef.current?.(value);
    resolverRef.current = null;
  };

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      <AlertDialog open={open} onOpenChange={(v) => !v && handle(false)}>
        <AlertDialogContent data-testid="confirm-dialog" className="rounded-none border-border">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-display text-2xl tracking-tight" data-testid="confirm-title">
              {opts.title}
            </AlertDialogTitle>
            <AlertDialogDescription className="text-sm text-muted-foreground" data-testid="confirm-description">
              {opts.description}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="gap-2">
            <AlertDialogCancel
              className="rounded-none border-border uppercase tracking-[0.18em] text-xs font-bold"
              onClick={() => handle(false)}
              data-testid="confirm-cancel"
            >
              {opts.cancelLabel}
            </AlertDialogCancel>
            <AlertDialogAction
              className={`rounded-none uppercase tracking-[0.18em] text-xs font-bold ${
                opts.destructive ? "bg-destructive text-destructive-foreground hover:bg-destructive/90" : ""
              }`}
              onClick={() => handle(true)}
              data-testid="confirm-ok"
            >
              {opts.confirmLabel}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </ConfirmContext.Provider>
  );
}

export function useConfirm() {
  const ctx = useContext(ConfirmContext);
  if (!ctx) throw new Error("useConfirm must be used within ConfirmProvider");
  return ctx;
}
