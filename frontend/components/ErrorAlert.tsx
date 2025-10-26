import styles from './ErrorAlert.module.css';

interface ErrorAlertProps {
  message: string;
}

export default function ErrorAlert({ message }: ErrorAlertProps) {
  if (!message) return null;
  
  return (
    <div className={styles.alert}>
      <p className={styles.title}>Error</p>
      <p className={styles.message}>{message}</p>
    </div>
  );
}
