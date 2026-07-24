/**
 * SweetAlert2 wrappers — consistent, brand-styled dialogs across the app.
 * The library CSS is imported once in main.tsx.
 */
import Swal from "sweetalert2";

const BRAND = "#4F46E5";

export function alertError(title: string, text?: string): Promise<unknown> {
  return Swal.fire({ icon: "error", title, text, confirmButtonColor: BRAND });
}

export function alertSuccess(title: string, text?: string): Promise<unknown> {
  return Swal.fire({ icon: "success", title, text, confirmButtonColor: BRAND, timer: 2200, timerProgressBar: true });
}

export function confirmDialog(title: string, text: string, confirmText = "Confirm"): Promise<boolean> {
  return Swal.fire({
    icon: "question",
    title,
    text,
    showCancelButton: true,
    confirmButtonText: confirmText,
    confirmButtonColor: BRAND,
    cancelButtonColor: "#64748b",
  }).then((r) => r.isConfirmed);
}
