interface ErrorAlertProps {
  message: string
  status?: number
}

export function ErrorAlert({ message, status }: ErrorAlertProps) {
  return (
    <div className="error-alert" role="alert">
      <strong>{status ? `Error ${status}` : 'Error'}</strong>
      <p>{message}</p>
    </div>
  )
}
