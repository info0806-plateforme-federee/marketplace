<script lang="ts">
	import * as m from '$lib/paraglide/messages';
	import { localizeHref } from '$lib/paraglide/runtime';
	import { enhance } from '$app/forms';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Textarea from '$lib/components/ui/Textarea.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import TagInput from '$lib/components/ui/TagInput.svelte';
	import Slider from '$lib/components/ui/Slider.svelte';

	let { form } = $props();

	const TOTAL_STEPS = 7;
	let currentStep = $state(1);
	let stepError = $state('');

	// --- Form state ---
	let name = $state('');
	let description = $state('');
	let category = $state('');
	let tags = $state('');
	let service_type = $state('');
	let execution_mode = $state('');
	let version = $state('1.0.0');
	let price_type = $state('');
	let price_amount = $state('');
	let currency = $state('EUR');
	let visibility = $state('');
	let input_schema = $state('');
	let output_schema = $state('');
	let image = $state('');
	let command = $state('');
	let code = $state('');
	let default_env = $state('');
	let default_args = $state('');
	let min_cpu = $state(0);
	let min_mem_mb = $state(0);
	let min_gpu = $state(0);
	let retry_count = $state(0);
	let max_concurrency = $state(1);
	let timeout_s = $state(30);
	let terms_of_use = $state('');

	// --- Option lists ---
	const serviceTypes = [
		{ value: 'compute', label: m.type_compute() },
		{ value: 'data', label: m.type_data() },
		{ value: 'model', label: m.type_model() },
		{ value: 'utility', label: m.type_utility() }
	];
	const priceTypes = [
		{ value: 'free', label: m.price_free() },
		{ value: 'fixed', label: 'Fixed per call' },
		{ value: 'time', label: 'Time-based' }
	];
	const visibilityOptions = [
		{ value: 'public', label: m.visibility_public() },
		{ value: 'private', label: m.visibility_private() },
		{ value: 'restricted', label: m.visibility_restricted() }
	];
	const executionModes = [
		{ value: 'sync', label: m.mode_sync() },
		{ value: 'async', label: m.mode_async() }
	];
	const categoryOptions = [
		{ value: 'ml', label: 'ML' },
		{ value: 'data-processing', label: 'Data Processing' },
		{ value: 'compute', label: 'Compute' },
		{ value: 'nlp', label: 'NLP' },
		{ value: 'computer-vision', label: 'Computer Vision' },
		{ value: 'analytics', label: 'Analytics' },
		{ value: 'storage', label: 'Storage' },
		{ value: 'other', label: 'Other' }
	];
	const currencyOptions = [
		{ value: 'EUR', label: 'EUR' },
		{ value: 'USD', label: 'USD' },
		{ value: 'GBP', label: 'GBP' },
		{ value: 'CHF', label: 'CHF' },
		{ value: 'JPY', label: 'JPY' }
	];
	const tagSuggestions = [
		'python',
		'gpu',
		'ml',
		'docker',
		'api',
		'data',
		'nlp',
		'vision',
		'realtime',
		'batch'
	];

	const stepLabels = [
		m.wizard_step_basic(),
		m.wizard_step_type(),
		m.wizard_step_pricing(),
		m.wizard_step_visibility(),
		m.wizard_step_schemas(),
		m.wizard_step_execution(),
		m.wizard_step_advanced()
	];

	function validateStep(step: number): boolean {
		stepError = '';
		switch (step) {
			case 1:
				if (!name.trim() || !category) {
					stepError = m.wizard_validation_required();
					return false;
				}
				break;
			case 2:
				if (!service_type || !execution_mode) {
					stepError = m.wizard_validation_required();
					return false;
				}
				break;
			case 3:
				if (!price_type) {
					stepError = m.wizard_validation_required();
					return false;
				}
				if (price_type !== 'free' && !price_amount) {
					stepError = m.wizard_validation_required();
					return false;
				}
				break;
			case 4:
				if (!visibility) {
					stepError = m.wizard_validation_required();
					return false;
				}
				break;
			case 5:
				try {
					if (input_schema.trim()) JSON.parse(input_schema);
					if (output_schema.trim()) JSON.parse(output_schema);
				} catch {
					stepError = m.wizard_validation_json();
					return false;
				}
				break;
		}
		return true;
	}

	function nextStep() {
		if (validateStep(currentStep)) {
			currentStep = Math.min(currentStep + 1, TOTAL_STEPS);
		}
	}

	function prevStep() {
		stepError = '';
		currentStep = Math.max(currentStep - 1, 1);
	}

	function goToStep(step: number) {
		stepError = '';
		currentStep = step;
	}

	function getLabelForValue(options: { value: string; label: string }[], val: string): string {
		return options.find((o) => o.value === val)?.label ?? val;
	}
</script>

<svelte:head>
	<title>{m.publish_title()}</title>
</svelte:head>

<PageHeader title={m.publish_title()} subtitle={m.publish_subtitle()}>
	{#snippet actions()}
		<Button variant="outline" href={localizeHref('/services')}>{m.common_back()}</Button>
	{/snippet}
</PageHeader>

<!-- Step indicator -->
<div class="mb-6 flex items-start">
	{#each stepLabels as label, i (i)}
		{@const step = i + 1}
		<!-- Connector line before step (except first) -->
		{#if i > 0}
			<div class="mt-4 h-0.5 flex-1 {step <= currentStep ? 'bg-emerald-500' : 'bg-secondary'}"></div>
		{/if}
		<!-- Step column: circle + label stacked -->
		<button
			type="button"
			class="flex w-16 shrink-0 flex-col items-center gap-1 sm:w-20"
			onclick={() => {
				if (step < currentStep) goToStep(step);
			}}
		>
			<div
				class="flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors
					{step === currentStep
					? 'bg-primary text-primary-foreground'
					: step < currentStep
						? 'bg-emerald-500 text-white'
						: 'bg-secondary text-muted-foreground'}"
			>
				{#if step < currentStep}
					&#10003;
				{:else}
					{step}
				{/if}
			</div>
			<span
				class="hidden text-center text-xs sm:block {step === currentStep
					? 'font-medium text-foreground'
					: 'text-muted-foreground'}">{label}</span
			>
		</button>
	{/each}
</div>

<Card>
	{#if form?.error}
		<div
			class="mb-4 rounded-md bg-red-100 p-3 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-400"
		>
			{form.error}
		</div>
	{/if}

	{#if stepError}
		<div
			class="mb-4 rounded-md bg-amber-100 p-3 text-sm text-amber-800 dark:bg-amber-900/30 dark:text-amber-400"
		>
			{stepError}
		</div>
	{/if}

	<p class="text-muted-foreground mb-4 text-sm">
		{m.wizard_step_n_of_total({ current: String(currentStep), total: String(TOTAL_STEPS) })}
	</p>

	<form method="POST" use:enhance class="space-y-6">
		<!-- Hidden inputs for all fields (always present for submission) -->
		<input type="hidden" name="name" value={name} />
		<input type="hidden" name="description" value={description} />
		<input type="hidden" name="category" value={category} />
		<input type="hidden" name="tags" value={tags} />
		<input type="hidden" name="service_type" value={service_type} />
		<input type="hidden" name="execution_mode" value={execution_mode} />
		<input type="hidden" name="version" value={version} />
		<input type="hidden" name="price_type" value={price_type} />
		<input type="hidden" name="price_amount" value={price_amount} />
		<input type="hidden" name="currency" value={currency} />
		<input type="hidden" name="visibility" value={visibility} />
		<input type="hidden" name="input_schema" value={input_schema} />
		<input type="hidden" name="output_schema" value={output_schema} />
		<input type="hidden" name="image" value={image} />
		<input type="hidden" name="command" value={command} />
		<input type="hidden" name="code" value={code} />
		<input type="hidden" name="default_env" value={default_env} />
		<input type="hidden" name="default_args" value={default_args} />
		<input type="hidden" name="min_cpu" value={String(min_cpu)} />
		<input type="hidden" name="min_mem_mb" value={String(min_mem_mb)} />
		<input type="hidden" name="min_gpu" value={String(min_gpu)} />
		<input type="hidden" name="retry_count" value={String(retry_count)} />
		<input type="hidden" name="max_concurrency" value={String(max_concurrency)} />
		<input type="hidden" name="timeout_s" value={String(timeout_s)} />
		<input type="hidden" name="terms_of_use" value={terms_of_use} />

		<!-- Step 1: Basic Info -->
		{#if currentStep === 1}
			<h2 class="text-foreground text-lg font-semibold">{m.wizard_step_basic()}</h2>
			<div class="space-y-4">
				<Input
					name="_name"
					label={m.publish_name()}
					bind:value={name}
					placeholder={m.publish_placeholder_name()}
					required
				/>
				<Textarea
					name="_description"
					label={m.publish_description()}
					bind:value={description}
					placeholder={m.publish_placeholder_description()}
					rows={3}
				/>
				<Select
					name="_category"
					label={m.publish_category()}
					options={categoryOptions}
					bind:value={category}
					placeholder="Select a category..."
					required
				/>
				<TagInput
					name="_tags"
					label={m.publish_tags()}
					bind:value={tags}
					placeholder={m.publish_tags_hint()}
					suggestions={tagSuggestions}
				/>
			</div>
		{/if}

		<!-- Step 2: Type & Execution -->
		{#if currentStep === 2}
			<h2 class="text-foreground text-lg font-semibold">{m.wizard_step_type()}</h2>
			<div class="space-y-4">
				<Select
					name="_service_type"
					label={m.publish_type()}
					options={serviceTypes}
					bind:value={service_type}
					placeholder="Select a type..."
					required
				/>
				<Select
					name="_execution_mode"
					label={m.publish_execution()}
					options={executionModes}
					bind:value={execution_mode}
					placeholder="Select a mode..."
					required
				/>
				<Input
					name="_version"
					label={m.publish_version()}
					bind:value={version}
					placeholder={m.publish_placeholder_version()}
				/>
			</div>
		{/if}

		<!-- Step 3: Pricing -->
		{#if currentStep === 3}
			<h2 class="text-foreground text-lg font-semibold">{m.wizard_step_pricing()}</h2>
			<div class="space-y-4">
				<Select
					name="_price_type"
					label={m.publish_pricing()}
					options={priceTypes}
					bind:value={price_type}
					placeholder="Select pricing model..."
					required
				/>
				{#if price_type && price_type !== 'free'}
					<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
						<Input
							name="_price_amount"
							label={m.publish_price_amount()}
							type="number"
							bind:value={price_amount}
							placeholder="0.00"
						/>
						<Select
							name="_currency"
							label={m.publish_currency()}
							options={currencyOptions}
							bind:value={currency}
						/>
					</div>
				{/if}
			</div>
		{/if}

		<!-- Step 4: Visibility -->
		{#if currentStep === 4}
			<h2 class="text-foreground text-lg font-semibold">{m.wizard_step_visibility()}</h2>
			<div class="space-y-4">
				<Select
					name="_visibility"
					label={m.publish_visibility()}
					options={visibilityOptions}
					bind:value={visibility}
					placeholder="Select visibility..."
					required
				/>
			</div>
		{/if}

		<!-- Step 5: Schemas -->
		{#if currentStep === 5}
			<h2 class="text-foreground text-lg font-semibold">{m.wizard_step_schemas()}</h2>
			<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
				<Textarea
					name="_input_schema"
					label={m.publish_input_schema()}
					bind:value={input_schema}
					placeholder={'{\n  "type": "object",\n  "properties": {\n    "text": { "type": "string" }\n  }\n}'}
					rows={8}
				/>
				<Textarea
					name="_output_schema"
					label={m.publish_output_schema()}
					bind:value={output_schema}
					placeholder={'{\n  "type": "object",\n  "properties": {\n    "result": { "type": "string" }\n  }\n}'}
					rows={8}
				/>
			</div>
		{/if}

		<!-- Step 6: Execution Config -->
		{#if currentStep === 6}
			<h2 class="text-foreground text-lg font-semibold">{m.wizard_step_execution()}</h2>
			<div class="space-y-4">
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
					<Input
						name="_image"
						label="Docker Image"
						bind:value={image}
						placeholder={m.publish_placeholder_image()}
					/>
					<Input
						name="_command"
						label="Command"
						bind:value={command}
						placeholder={m.publish_placeholder_command()}
					/>
				</div>
				<Textarea
					name="_code"
					label="Code"
					bind:value={code}
					placeholder={'import json\nimport sys\n\ndata = json.load(sys.stdin)\nprint(json.dumps({"result": data}))'}
					rows={6}
				/>
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
					<Textarea
						name="_default_env"
						label="Default Environment (JSON)"
						bind:value={default_env}
						placeholder={'{\n  "PYTHONUNBUFFERED": "1",\n  "LOG_LEVEL": "info"\n}'}
						rows={4}
					/>
					<Textarea
						name="_default_args"
						label="Default Arguments (JSON)"
						bind:value={default_args}
						placeholder={'{\n  "batch_size": 32,\n  "verbose": true\n}'}
						rows={4}
					/>
				</div>
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
					<Slider
						name="_min_cpu"
						label="Min CPU"
						min={0}
						max={16}
						step={1}
						bind:value={min_cpu}
						unit="cores"
					/>
					<Slider
						name="_min_mem_mb"
						label="Min Memory"
						min={0}
						max={16384}
						step={256}
						bind:value={min_mem_mb}
						unit="MB"
					/>
				</div>
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
					<Slider
						name="_min_gpu"
						label="Min GPU"
						min={0}
						max={8}
						step={1}
						bind:value={min_gpu}
						unit="GPUs"
					/>
					<Slider
						name="_retry_count"
						label="Retry Count"
						min={0}
						max={10}
						step={1}
						bind:value={retry_count}
						unit="retries"
					/>
				</div>
			</div>
		{/if}

		<!-- Step 7: Advanced & Summary -->
		{#if currentStep === 7}
			<h2 class="text-foreground text-lg font-semibold">{m.wizard_step_advanced()}</h2>
			<div class="space-y-4">
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
					<Slider
						name="_max_concurrency"
						label={m.publish_max_concurrency()}
						min={1}
						max={100}
						step={1}
						bind:value={max_concurrency}
						unit="slots"
					/>
					<Slider
						name="_timeout_s"
						label={m.publish_timeout()}
						min={5}
						max={3600}
						step={5}
						bind:value={timeout_s}
						unit="s"
					/>
				</div>
				<Textarea
					name="_terms_of_use"
					label={m.publish_terms()}
					bind:value={terms_of_use}
					placeholder={m.publish_placeholder_terms()}
					rows={3}
				/>
			</div>

			<!-- Summary -->
			<div class="border-border mt-6 border-t pt-6">
				<h3 class="text-foreground mb-4 text-lg font-semibold">{m.wizard_summary()}</h3>
				<div class="space-y-4">
					<!-- Basic Info -->
					<div class="border-border rounded-md border p-4">
						<div class="mb-2 flex items-center justify-between">
							<h4 class="text-foreground text-sm font-medium">{m.wizard_step_basic()}</h4>
							<button
								type="button"
								class="text-primary text-xs hover:underline"
								onclick={() => goToStep(1)}>{m.wizard_edit_step()}</button
							>
						</div>
						<dl class="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
							<dt class="text-muted-foreground">{m.publish_name()}</dt>
							<dd class="text-foreground">{name || '—'}</dd>
							<dt class="text-muted-foreground">{m.publish_category()}</dt>
							<dd class="text-foreground">{getLabelForValue(categoryOptions, category) || '—'}</dd>
							<dt class="text-muted-foreground">{m.publish_tags()}</dt>
							<dd>
								{#if tags}
									<span class="flex flex-wrap gap-1">
										{#each tags
											.split(',')
											.map((t) => t.trim())
											.filter(Boolean) as tag (tag)}
											<Badge variant="secondary">{tag}</Badge>
										{/each}
									</span>
								{:else}
									<span class="text-foreground">—</span>
								{/if}
							</dd>
						</dl>
						{#if description}
							<p class="text-muted-foreground mt-2 text-sm">{description}</p>
						{/if}
					</div>

					<!-- Type & Execution -->
					<div class="border-border rounded-md border p-4">
						<div class="mb-2 flex items-center justify-between">
							<h4 class="text-foreground text-sm font-medium">{m.wizard_step_type()}</h4>
							<button
								type="button"
								class="text-primary text-xs hover:underline"
								onclick={() => goToStep(2)}>{m.wizard_edit_step()}</button
							>
						</div>
						<dl class="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
							<dt class="text-muted-foreground">{m.publish_type()}</dt>
							<dd class="text-foreground">{getLabelForValue(serviceTypes, service_type) || '—'}</dd>
							<dt class="text-muted-foreground">{m.publish_execution()}</dt>
							<dd class="text-foreground">
								{getLabelForValue(executionModes, execution_mode) || '—'}
							</dd>
							<dt class="text-muted-foreground">{m.publish_version()}</dt>
							<dd class="text-foreground">{version || '—'}</dd>
						</dl>
					</div>

					<!-- Pricing -->
					<div class="border-border rounded-md border p-4">
						<div class="mb-2 flex items-center justify-between">
							<h4 class="text-foreground text-sm font-medium">{m.wizard_step_pricing()}</h4>
							<button
								type="button"
								class="text-primary text-xs hover:underline"
								onclick={() => goToStep(3)}>{m.wizard_edit_step()}</button
							>
						</div>
						<dl class="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
							<dt class="text-muted-foreground">{m.publish_pricing()}</dt>
							<dd class="text-foreground">{getLabelForValue(priceTypes, price_type) || '—'}</dd>
							{#if price_type !== 'free' && price_amount}
								<dt class="text-muted-foreground">{m.publish_price_amount()}</dt>
								<dd class="text-foreground">{price_amount} {currency}</dd>
							{/if}
						</dl>
					</div>

					<!-- Visibility -->
					<div class="border-border rounded-md border p-4">
						<div class="mb-2 flex items-center justify-between">
							<h4 class="text-foreground text-sm font-medium">{m.wizard_step_visibility()}</h4>
							<button
								type="button"
								class="text-primary text-xs hover:underline"
								onclick={() => goToStep(4)}>{m.wizard_edit_step()}</button
							>
						</div>
						<dl class="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
							<dt class="text-muted-foreground">{m.publish_visibility()}</dt>
							<dd class="text-foreground">
								{getLabelForValue(visibilityOptions, visibility) || '—'}
							</dd>
						</dl>
					</div>

					<!-- Execution Config -->
					{#if image || code || command}
						<div class="border-border rounded-md border p-4">
							<div class="mb-2 flex items-center justify-between">
								<h4 class="text-foreground text-sm font-medium">{m.wizard_step_execution()}</h4>
								<button
									type="button"
									class="text-primary text-xs hover:underline"
									onclick={() => goToStep(6)}>{m.wizard_edit_step()}</button
								>
							</div>
							<dl class="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
								{#if image}
									<dt class="text-muted-foreground">Docker Image</dt>
									<dd class="text-foreground">{image}</dd>
								{/if}
								{#if command}
									<dt class="text-muted-foreground">Command</dt>
									<dd class="text-foreground">{command}</dd>
								{/if}
								<dt class="text-muted-foreground">Resources</dt>
								<dd class="text-foreground">{min_cpu} CPU, {min_mem_mb} MB, {min_gpu} GPU</dd>
							</dl>
						</div>
					{/if}
				</div>
			</div>
		{/if}

		<!-- Navigation -->
		<div class="border-border flex justify-between border-t pt-4">
			<div>
				{#if currentStep > 1}
					<Button type="button" variant="outline" onclick={prevStep}>{m.wizard_previous()}</Button>
				{:else}
					<Button variant="outline" href={localizeHref('/services')}>{m.common_cancel()}</Button>
				{/if}
			</div>
			<div>
				{#if currentStep < TOTAL_STEPS}
					<Button type="button" onclick={nextStep}>{m.wizard_next()}</Button>
				{:else}
					<Button type="submit">{m.publish_submit()}</Button>
				{/if}
			</div>
		</div>
	</form>
</Card>
