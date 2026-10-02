export const DOCUMENT_TYPES = [
  'rti', 'fir', 'consumer', 'electricity', 'rent', 'scholarship', 'pension', 'cybercrime',
] as const;

export type DocumentType = (typeof DOCUMENT_TYPES)[number];

export interface DocumentFormValues {
  docType: DocumentType;
  department: string;
  name: string;
  phone: string;
  address: string;
  issue: string;
}

export function buildTemplateData(formValues: DocumentFormValues): Record<string, string | number> {
  const today = new Date().toISOString().slice(0, 10);
  const fullName = formValues.name;

  const base = {
    date: today,
    name: fullName,
    applicant_name: fullName,
    applicant_address: formValues.address,
    address: formValues.address,
    phone: formValues.phone,
    email: 'citizen@example.com',
    issue_details: formValues.issue,
    issue_summary: formValues.issue,
    office_address: formValues.address,
    department: formValues.department || 'Concerned Department',
    district: 'District Office',
    utility_name: formValues.department || 'Electricity Department',
  };

  const byType: Record<DocumentType, Record<string, string | number>> = {
    rti: {
      department: formValues.department || 'Public Information Officer',
      address: formValues.address,
      query_details: formValues.issue,
      specific_question_1: 'Provide complete file noting related to this matter.',
      specific_question_2: 'Provide current status with expected completion date.',
      specific_question_3: 'Provide names/designations of responsible officials.',
      payment_mode: 'Postal Order',
      applicant_name: fullName,
      applicant_address: formValues.address,
      place: 'India',
    },
    fir: {
      district: 'District Police Office',
      offense_nature: 'cognizable offense',
      incident_date: today,
      police_station: formValues.department || 'Local Police Station',
      incident_description: formValues.issue,
      ipc_sections: 'relevant IPC sections',
      officer_name: 'Duty Officer',
      reason_given: 'no valid reason',
      address: formValues.address,
    },
    consumer: {
      year: new Date().getFullYear(),
      complainant_name: fullName,
      company_name: formValues.department || 'Service Provider',
      defect_description: formValues.issue,
      refund_or_replacement: 'Refund/replacement and corrective service',
      amount: '50000',
      purchase_date: today,
      product: 'Product/Service',
      price: '0',
      defect_date: today,
      defect_details: formValues.issue,
      complaint_date: today,
      value: '0',
      signature: fullName,
    },
    electricity: {
      utility_name: formValues.department || 'Electricity Department',
      consumer_number: 'NA',
      issue_summary: formValues.issue,
      issue_details: formValues.issue,
      name: fullName,
    },
    rent: {
      landlord_name: 'Landlord Name',
      landlord_address: formValues.address,
      tenant_name: fullName,
      property_address: formValues.address,
      facts: formValues.issue,
    },
    scholarship: {
      department: formValues.department || 'Scholarship Department',
      academic_year: String(new Date().getFullYear()),
      student_name: fullName,
      institution: 'Institute Name',
      application_id: 'NA',
      issue_details: formValues.issue,
    },
    pension: {
      department: formValues.department || 'Pension Department',
      ppo_number: 'NA',
      applicant_name: fullName,
      account_last4: '0000',
      issue_details: formValues.issue,
    },
    cybercrime: {
      district: 'Cyber Crime Cell',
      incident_type: 'online fraud',
      name: fullName,
      phone: formValues.phone,
      email: 'citizen@example.com',
      incident_details: formValues.issue,
    },
  };

  return { ...base, ...byType[formValues.docType] };
}
